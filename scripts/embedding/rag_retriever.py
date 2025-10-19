# scripts/embedding/rag_retriever.py
from __future__ import annotations

import logging
from pathlib import Path
import pickle
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class StaticsMechanicsRAG:
    """
    Renal-focused retriever. Class name kept for app import compatibility.
    Safe against NumPy truth-value errors. Rebuilds doc embeddings if needed.
    """

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.model_name = "all-MiniLM-L6-v2"  # 384 dims
        self.encoder: Optional[SentenceTransformer] = None

        # Unified in-memory store
        self.embeddings_data: Dict[str, Any] = {
            "documents": [],                  # List[str]
            "embeddings": np.zeros((0, 384), dtype=np.float32),  # np.ndarray [N, D]
            "metadatas": [],                  # List[dict]
            "ids": [],                        # List[int]
        }

        self._load_embeddings()

    # Prevent boolean ambiguity if someone does "if retriever:"
    def __bool__(self) -> bool:
        try:
            return len(self.embeddings_data.get("documents", [])) > 0
        except Exception:
            return False

    # ---------------- Public API used by the TA ----------------

    def get_concept_related_content(self, query: str, n_results: int = 8) -> List[Dict[str, Any]]:
        return self.retrieve_relevant_content(query, n_results=n_results, tag_as="course_slide")

    def get_similar_exercises(self, query: str, n_results: int = 2) -> List[Dict[str, Any]]:
        return self.retrieve_relevant_content(query, n_results=n_results, tag_as="exercise_question")

    def get_solution_guidance(self, query: str, n_results: int = 2) -> List[Dict[str, Any]]:
        return self.retrieve_relevant_content(query, n_results=n_results, tag_as="exercise_solution")

    # ---------------- Core retrieval ----------------

    def retrieve_relevant_content(
        self, query: str, n_results: int = 8, tag_as: str | None = None
    ) -> List[Dict[str, Any]]:
        docs: List[str] = self.embeddings_data.get("documents", [])
        embs: np.ndarray = self.embeddings_data.get("embeddings", np.zeros((0, 384), dtype=np.float32))
        metas: List[Dict[str, Any]] = self.embeddings_data.get("metadatas", [])

        if len(docs) == 0:
            logger.warning("No documents loaded; returning renal fallback content.")
            return self._get_fallback_content(tag_as)

        # Ensure we have doc embeddings with the right shape
        embs = self._ensure_doc_embeddings(docs, embs)
        if not isinstance(embs, np.ndarray) or embs.size == 0:
            logger.warning("No usable embeddings after normalization; returning renal fallback content.")
            return self._get_fallback_content(tag_as)

        qvec = self._encode_query(query)
        if qvec is None or not isinstance(qvec, np.ndarray) or qvec.size == 0:
            logger.warning("Query encoding failed; returning renal fallback content.")
            return self._get_fallback_content(tag_as)

        try:
            boost = self._keyword_boost(query, docs)
            sims = cosine_similarity(qvec, embs)[0] * boost
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return self._get_fallback_content(tag_as)

        k = max(1, int(n_results or 8))
        top_idx = np.argsort(-sims)[:k]

        results: List[Dict[str, Any]] = []
        for i in top_idx:
            text = docs[i] if i < len(docs) else ""
            meta = (metas[i] if i < len(metas) else {}) or {}
            if tag_as:
                meta = meta.copy()
                meta["content_type"] = tag_as
            results.append({
                "text": str(text),
                "metadata": meta,
                "similarity_score": float(sims[i]),
                "source": meta.get("source_file") or meta.get("source") or "unknown",
            })

        if not any((r.get("text") or "").strip() for r in results):
            return self._get_fallback_content(tag_as)

        return results

    # ---------------- Load / normalize persisted data ----------------

    def _load_embeddings(self) -> None:
        emb_dir = self.base_path / "embeddings"
        pkl_legacy = emb_dir / "embeddings_data.pkl"  # legacy schema
        pkl_kb = emb_dir / "kb.pkl"                   # new schema from your builder

        try:
            if pkl_legacy.exists():
                with open(pkl_legacy, "rb") as f:
                    data = pickle.load(f)
                self._normalize_legacy(data)
                logger.info(f"Loaded {len(self.embeddings_data['documents'])} docs (embeddings_data.pkl)")
                return

            if pkl_kb.exists():
                with open(pkl_kb, "rb") as f:
                    kb = pickle.load(f)
                self._normalize_kb(kb)
                logger.info(f"Loaded {len(self.embeddings_data['documents'])} docs (kb.pkl)")
                return

            logger.warning("No embeddings pickle found in 'embeddings/'. Using renal fallbacks.")
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")

    def _normalize_legacy(self, data: Dict[str, Any]) -> None:
        docs_raw = data.get("documents", [])
        embs_raw = data.get("embeddings", None)
        metas_raw = data.get("metadatas", None)

        docs = list(docs_raw)
        embs = np.asarray(embs_raw, dtype=np.float32) if embs_raw is not None else np.zeros((0, 384), dtype=np.float32)
        if embs.ndim != 2:
            embs = np.zeros((0, 384), dtype=np.float32)

        metas = list(metas_raw) if metas_raw is not None else [{} for _ in docs]
        ids = list(range(len(docs)))

        self.embeddings_data = {
            "documents": docs,
            "embeddings": embs,
            "metadatas": metas,
            "ids": ids,
        }

    def _normalize_kb(self, kb: Dict[str, Any]) -> None:
        # kb: {"spans":[{"doc":..., "chunk":..., "text":...}, ...], "embeddings":[...], "docs":[...]}
        spans = kb.get("spans", [])
        embs_raw = kb.get("embeddings", None)

        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for s in spans:
            if isinstance(s, dict):
                text = s.get("text", "")
                src = s.get("doc") or s.get("name") or "unknown"
            else:
                text, src = str(s), "unknown"
            documents.append(text)
            metadatas.append({
                "source_file": src,
                "content_type": "course_slide",
                "topic": "renal",
            })

        # We intentionally IGNORE stored embeddings here if their shape won't match MiniLM.
        # We'll rebuild with MiniLM on demand to guarantee matching dimensions.
        embs = np.asarray(embs_raw, dtype=np.float32) if embs_raw is not None else np.zeros((0, 384), dtype=np.float32)
        if embs.ndim != 2:
            embs = np.zeros((0, 384), dtype=np.float32)

        self.embeddings_data = {
            "documents": documents,
            "embeddings": embs,  # may be empty; will be rebuilt with MiniLM at first retrieval
            "metadatas": metadatas,
            "ids": list(range(len(documents))),
        }

    # ---------------- Ensure doc embeddings are compatible ----------------

    def _ensure_doc_embeddings(self, docs: List[str], embs: np.ndarray) -> np.ndarray:
        """
        Ensure: non-empty, shape (len(docs), 384). Rebuild with MiniLM if needed.
        """
        need_rebuild = False
        if not isinstance(embs, np.ndarray):
            need_rebuild = True
        elif embs.ndim != 2:
            need_rebuild = True
        elif embs.shape[0] != len(docs):
            need_rebuild = True
        elif embs.shape[1] != 384:
            need_rebuild = True

        if not need_rebuild:
            return embs

        if len(docs) == 0:
            return np.zeros((0, 384), dtype=np.float32)

        try:
            self._lazy_load_encoder()
            logger.info("Rebuilding document embeddings with MiniLM (one-time).")
            # Batch encode to avoid memory spikes
            batch = 64
            vecs: List[np.ndarray] = []
            for i in range(0, len(docs), batch):
                chunk = docs[i:i + batch]
                enc = self.encoder.encode(chunk, normalize_embeddings=True)
                vecs.append(np.asarray(enc, dtype=np.float32))
            rebuilt = np.vstack(vecs) if vecs else np.zeros((len(docs), 384), dtype=np.float32)
            # Persist in memory
            self.embeddings_data["embeddings"] = rebuilt
            return rebuilt
        except Exception as e:
            logger.error(f"Failed to rebuild document embeddings: {e}")
            return np.zeros((0, 384), dtype=np.float32)

    # ---------------- Encoder and query vector ----------------

    def _lazy_load_encoder(self) -> None:
        if self.encoder is None:
            logger.info("Initializing SentenceTransformer on device: cpu")
            self.encoder = SentenceTransformer(self.model_name)
            logger.info("SentenceTransformer model initialized")

    def _encode_query(self, query: str) -> Optional[np.ndarray]:
        try:
            self._lazy_load_encoder()
            vec = self.encoder.encode([query], normalize_embeddings=True)
            arr = np.asarray(vec, dtype=np.float32)
            return arr  # shape (1, 384)
        except Exception as e:
            logger.error(f"Query encoding failed: {e}")
            return None

    # ---------------- Simple keyword prior ----------------

    def _keyword_boost(self, query: str, docs: List[str]) -> np.ndarray:
        q = (query or "").lower()
        n = max(1, len(docs))
        boost = np.ones(n, dtype=np.float32)

        renal_terms = [
            "renal", "kidney", "nephron", "glomerul", "tubule", "henle",
            "gfr", "clearance", "raas", "diuretic", "osm", "urine",
            "reabsorption", "secretion", "filtration", "collecting duct",
        ]

        if any(t in q for t in renal_terms):
            for i, d in enumerate(docs):
                dl = (d or "").lower()
                hits = sum(t in dl for t in renal_terms)
                if hits:
                    boost[i] += 0.05 * min(6, hits)  # cap +0.3
        return boost

    # ---------------- Renal fallback content ----------------

    def _get_fallback_content(self, tag_as: str | None = None) -> List[Dict[str, Any]]:
        base = [
            {
                "text": (
                    "Glomerular filtration depends on capillary hydrostatic pressure (P_GC), "
                    "Bowman's space pressure (P_BS), and plasma oncotic pressure (π_GC). "
                    "Relation: $\\text{GFR} = K_f\\,(P_{GC} - P_{BS} - \\pi_{GC})$."
                ),
                "metadata": {
                    "content_type": "course_slide",
                    "topic": "GFR determinants",
                    "source_file": "renal_overview.md",
                },
                "similarity_score": 0.70,
                "source": "renal_overview.md",
            },
            {
                "text": (
                    "The loop of Henle establishes the corticomedullary gradient via countercurrent multiplication "
                    "and urea recycling. The thick ascending limb reabsorbs NaCl without water, concentrating the medulla."
                ),
                "metadata": {
                    "content_type": "course_slide",
                    "topic": "Countercurrent mechanism",
                    "source_file": "henle_notes.md",
                },
                "similarity_score": 0.65,
                "source": "henle_notes.md",
            },
            {
                "text": (
                    "Clearance formulas: $C_x = \\dfrac{U_x V}{P_x}$ and "
                    "$C_{\\mathrm{osm}} = \\dfrac{U_{\\mathrm{osm}} V}{P_{\\mathrm{osm}}}$. "
                    "Free water clearance: $\\dot{V}_{H2O} = V - C_{\\mathrm{osm}}$."
                ),
                "metadata": {
                    "content_type": "exercise_solution",
                    "topic": "Clearance calculations",
                    "source_file": "clearance_solutions.md",
                },
                "similarity_score": 0.60,
                "source": "clearance_solutions.md",
            },
        ]
        if tag_as:
            for b in base:
                b["metadata"]["content_type"] = tag_as
        return base

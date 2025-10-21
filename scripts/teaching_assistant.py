# scripts/teaching_assistant.py
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI

# Retriever and storage
from .embedding.rag_retriever import StaticsMechanicsRAG
from .database.conversation_storage import conversation_storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NOT_RELEVANT_MSG = "This question is not relevant to renal physiology."

RENAL_SYSTEM_PROMPT = """
You are ARIA, an Academic Tutor for Renal Physiology and Pathophysiology.
Answer strictly from the provided context chunks built from local files.
If the context is insufficient, say so briefly. Be concise and factual.
Always format equations with LaTeX when applicable.
Example: $\\text{GFR} = K_f\\,(P_{GC} - P_{BS} - \\pi_{GC})$
""".strip()


class StaticsMechanicsTA:
    """
    Renal-focused teaching assistant.
    Class name kept for backward compatibility with app imports.
    """

    def __init__(self, base_path: str, api_key: str):
        self.base_path = Path(base_path)
        self.rag = StaticsMechanicsRAG(base_path)
        self.client = OpenAI(api_key=api_key)
        self.session_id = str(uuid.uuid4())
        self.system_prompt = RENAL_SYSTEM_PROMPT

    # ---------- Public API ----------

    def generate_response(
        self,
        student_question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        start_time = datetime.now(timezone.utc)

        try:
            # Always relevant
            is_course_relevant = self._is_question_course_relevant(student_question)
            logger.info(
                f"Course relevance decision: {is_course_relevant} for question: '{student_question[:100]}'"
            )

            relevant_content = self._get_relevant_content(student_question)
            logger.info(
                f"Retrieved {len(relevant_content)} chunks; "
                f"sources={[c.get('metadata',{}).get('source_file','?') for c in relevant_content]}"
            )

            context = self._prepare_context(relevant_content)
            messages = self._create_messages(student_question, context, conversation_history)

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
                temperature=0.2,
                presence_penalty=0.0,
                frequency_penalty=0.0,
                top_p=1.0,
            )
            assistant_response = (response.choices[0].message.content or "").strip()

            # Append sources when context was used
            if assistant_response and relevant_content:
                src = self._format_source_references(relevant_content)
                if src:
                    assistant_response += f"\n\n📚 **Sources:** {src}"

            response_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._log_interaction(student_question, assistant_response, relevant_content, response_time)

            return {
                "response": assistant_response or "The context provided does not contain relevant information.",
                "relevant_topics": [c.get("metadata", {}).get("topic", "Unknown") for c in relevant_content],
                "concepts_covered": self._extract_concepts_from_content(relevant_content),
                "suggested_review": self._suggest_review_materials(relevant_content),
                "is_course_relevant": True,
                "context_sources": [c.get("metadata", {}).get("source_file", "unknown") for c in relevant_content],
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "Technical issue while processing the question.",
                "error": str(e),
                "is_course_relevant": True,
            }

    def get_session_id(self) -> str:
        return self.session_id

    def new_session(self) -> str:
        self.session_id = str(uuid.uuid4())
        logger.info(f"Started new session: {self.session_id}")
        return self.session_id

    # ---------- Retrieval and context ----------

    def _get_relevant_content(self, question: str) -> List[Dict[str, Any]]:
        # Permissive, higher recall
        concept = self.rag.get_concept_related_content(question, n_results=8)
        exercises = self.rag.get_similar_exercises(question, n_results=2)
        guidance = self.rag.get_solution_guidance(question, n_results=2)
        all_content = (concept or []) + (exercises or []) + (guidance or [])
        # Keep textual, drop empties, deduplicate
        out = [c for c in all_content if isinstance(c, dict) and (c.get("text") or "").strip()]
        return self._deduplicate_content(out)[:8]

    def _prepare_context(self, relevant_content: List[Dict[str, Any]]) -> str:
        parts = []
        for c in relevant_content:
            meta = c.get("metadata", {}) or {}
            ctype = meta.get("content_type", "context").upper()
            topic = meta.get("topic", "Untitled")
            text = c.get("text", "")
            seg = f"\n--- {ctype}: {topic} ---\n{text}"
            parts.append(seg)
        return "\n".join(parts)

    # ---------- Prompt construction ----------

    def _create_messages(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [{"role": "system", "content": self.system_prompt}]

        if conversation_history:
            messages.extend(conversation_history[-6:])

        # f-string with escaped braces for LaTeX
        user_message = f"""
Student Question: {question}

Context (from local renal files):
{context}

Provide a direct, source-grounded answer. If the context lacks the answer, state that briefly.

1. **Concept Explanation**: Summarize the renal physiology involved (e.g., filtration, reabsorption, secretion, RAAS) in concise, factual terms.
2. **Key Factors / Steps**: List the main determinants or steps (e.g., pressures, transporters, nephron segments, hormones).
3. **Mechanisms**: Explicitly state the order and timing of the mechanisms (e.g, Myogenic Mechanism: Instantaneous, Tubuloglomerular Feedback (TGF): Slower (seconds to minutes), 
RAAS: Slowest (minutes to hours, hormonal).).

Citations:
- End with 'Sources:' and list filenames or section titles of the used chunks.

Answer style: concise, academic, no speculation or tutoring scaffolds.
""".strip()
        messages.append({"role": "user", "content": user_message})
        return messages

    # ---------- Relevance gate (disabled) ----------

    def _is_question_course_relevant(self, question: str) -> bool:
        """Disable relevance filtering; treat every question as valid."""
        return True

    # ---------- Utilities ----------

    def _deduplicate_content(self, content_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique, seen = [], set()
        for c in content_list or []:
            key = hash(((c.get("text") or "")[:400], c.get("metadata", {}).get("source_file", "")))
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def _format_source_references(self, content_list: List[Dict[str, Any]]) -> str:
        names = []
        for c in content_list or []:
            meta = c.get("metadata", {}) or {}
            src = meta.get("source_file") or meta.get("source") or "unknown"
            # Clean up filename-ish strings
            src = Path(src).stem.replace("_", " ").title()
            if src not in names:
                names.append(src)
        if not names:
            return ""
        # Show up to 3 unique sources
        names = names[:3]
        if len(names) == 1:
            return names[0]
        return "; ".join(f"[{i+1}] {n}" for i, n in enumerate(names))

    def _extract_concepts_from_content(self, content_list: List[Dict[str, Any]]) -> List[str]:
        out = set()
        for c in content_list or []:
            for k in c.get("metadata", {}).get("concepts", []) or []:
                if k:
                    out.add(k)
        return list(out)

    def _suggest_review_materials(self, content_list: List[Dict[str, Any]]) -> List[str]:
        topics = set()
        for c in content_list or []:
            t = c.get("metadata", {}).get("topic", "")
            if t:
                topics.add(t)
        return list(topics)

    # ---------- Logging ----------

    def _log_interaction(
        self,
        question: str,
        response: str,
        context: List[Dict[str, Any]],
        response_time: Optional[float] = None
    ):
        try:
            context_sources = [c.get("metadata", {}).get("source_file", "unknown") for c in context or []]
            concepts_used = self._extract_concepts_from_content(context or [])

            ok = conversation_storage.store_conversation(
                session_id=self.session_id,
                user_question=question,
                ta_response=response,
                context_sources=context_sources,
                concepts_used=concepts_used,
                response_time=response_time,
            )

            if ok:
                logger.info("Conversation logged to Supabase successfully")
            else:
                logger.warning("Failed to log conversation to Supabase, falling back to local logging")
                self._fallback_log_interaction(question, response, context_sources, concepts_used, response_time)

        except Exception as e:
            logger.error(f"Error logging to Supabase: {e}")
            self._fallback_log_interaction(question, response, [], [], response_time)

    def _fallback_log_interaction(
        self,
        question: str,
        response: str,
        context_sources: List[str],
        concepts_used: List[str],
        response_time: Optional[float] = None
    ):
        try:
            log_entry = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "session_id": self.session_id,
                "question": question,
                "response_length": len(response or ""),
                "context_sources": context_sources or [],
                "concepts_used": concepts_used or [],
                "response_time_s": float(response_time) if response_time is not None else None,
            }
            log_file = self.base_path / "logs" / "ta_interactions.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            logger.info("Conversation logged to local file successfully")
        except Exception as e:
            logger.error(f"Failed to log conversation even to local file: {e}")

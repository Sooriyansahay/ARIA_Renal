import json
import os
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import hashlib
from tqdm import tqdm
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CourseContentEmbedder:
    def __init__(self, base_path: str, model_name: str = "all-MiniLM-L6-v2"):
        self.base_path = Path(base_path)
        self.model = SentenceTransformer(model_name)
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.base_path / "embeddings" / "chroma_db")
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="statics_mechanics_content",
            metadata={"hnsw:space": "cosine"}
        )
        
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Smart chunking that preserves sentence boundaries"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        # Add overlap between chunks
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i > 0 and overlap > 0:
                prev_words = chunks[i-1].split()[-overlap:]
                chunk = " ".join(prev_words) + " " + chunk
            overlapped_chunks.append(chunk)
            
        return overlapped_chunks
    
    def extract_metadata(self, file_path: str, content: Dict) -> Dict[str, Any]:
        """Extract rich metadata for better retrieval"""
        metadata = {
            "source_file": file_path,
            "content_type": "course_slide" if "course_slides" in file_path else "exercise",
            "topic": content.get("topic", ""),
            "difficulty": "intermediate",  # Can be enhanced with ML classification
            "concepts": "",  # Convert to comma-separated string
            "formulas": "",  # Convert to comma-separated string
            "examples": ""   # Convert to comma-separated string
        }
        
        # Extract concepts from content
        text_content = str(content)
        concepts = self._extract_concepts(text_content)
        metadata["concepts"] = ", ".join(concepts)  # Convert list to string
        
        # Extract formulas
        formulas = self._extract_formulas(content)
        metadata["formulas"] = ", ".join(formulas)  # Convert list to string
        
        return metadata
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key engineering concepts"""
        key_terms = [
            "stress", "strain", "moment", "force", "equilibrium", "deflection",
            "torsion", "bending", "shear", "axial", "centroid", "inertia",
            "beam", "truss", "frame", "column", "buckling", "fatigue"
        ]
        
        found_concepts = []
        text_lower = text.lower()
        for term in key_terms:
            if term in text_lower:
                found_concepts.append(term)
        
        return found_concepts
    
    def _extract_formulas(self, content: Dict) -> List[str]:
        """Extract mathematical formulas from content"""
        formulas = []
        
        # Look for formula sections in the content
        if isinstance(content, dict):
            for key, value in content.items():
                if "formula" in key.lower() or "equation" in key.lower():
                    if isinstance(value, str):
                        formulas.append(value)
                    elif isinstance(value, list):
                        formulas.extend([str(v) for v in value])
        
        return formulas
    
    def process_course_slides(self) -> List[Dict]:
        """Process all course slide content"""
        slides_path = self.base_path / "processed_content" / "course_slides"
        documents = []
        
        for topic_dir in slides_path.iterdir():
            if topic_dir.is_dir():
                json_file = topic_dir / f"{topic_dir.name}_extracted.json"
                if json_file.exists():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                        
                        # Extract text content
                        text_content = self._extract_text_from_content(content)
                        
                        # Create chunks
                        chunks = self.chunk_text(text_content)
                        
                        # Extract metadata
                        metadata = self.extract_metadata(str(json_file), content)
                        
                        for i, chunk in enumerate(chunks):
                            doc = {
                                "id": f"slide_{topic_dir.name}_{i}",
                                "text": chunk,
                                "metadata": {**metadata, "chunk_index": i}
                            }
                            documents.append(doc)
                            
                    except Exception as e:
                        logger.error(f"Error processing {json_file}: {e}")
        
        return documents
    
    def process_exercises(self) -> List[Dict]:
        """Process all exercise content"""
        exercises_path = self.base_path / "processed_content" / "exercises"
        documents = []
        
        for exercise_dir in exercises_path.iterdir():
            if exercise_dir.is_dir():
                json_file = exercise_dir / f"{exercise_dir.name}_extracted.json"
                if json_file.exists():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                        
                        # Process questions and solutions separately
                        if "questions" in content:
                            for q_idx, question in enumerate(content["questions"]):
                                text_content = self._extract_text_from_content(question)
                                chunks = self.chunk_text(text_content)
                                
                                metadata = self.extract_metadata(str(json_file), question)
                                metadata["content_type"] = "exercise_question"
                                metadata["exercise_number"] = exercise_dir.name
                                metadata["question_index"] = q_idx
                                
                                for i, chunk in enumerate(chunks):
                                    doc = {
                                        "id": f"exercise_{exercise_dir.name}_q{q_idx}_{i}",
                                        "text": chunk,
                                        "metadata": {**metadata, "chunk_index": i}
                                    }
                                    documents.append(doc)
                        
                        if "solutions" in content:
                            for s_idx, solution in enumerate(content["solutions"]):
                                text_content = self._extract_text_from_content(solution)
                                chunks = self.chunk_text(text_content)
                                
                                metadata = self.extract_metadata(str(json_file), solution)
                                metadata["content_type"] = "exercise_solution"
                                metadata["exercise_number"] = exercise_dir.name
                                metadata["solution_index"] = s_idx
                                
                                for i, chunk in enumerate(chunks):
                                    doc = {
                                        "id": f"exercise_{exercise_dir.name}_s{s_idx}_{i}",
                                        "text": chunk,
                                        "metadata": {**metadata, "chunk_index": i}
                                    }
                                    documents.append(doc)
                                    
                    except Exception as e:
                        logger.error(f"Error processing {json_file}: {e}")
        
        return documents
    
    def _extract_text_from_content(self, content: Any) -> str:
        """Extract readable text from various content formats"""
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            text_parts = []
            for key, value in content.items():
                if key in ["text", "content", "description", "explanation"]:
                    text_parts.append(str(value))
                elif isinstance(value, (str, list)):
                    text_parts.append(str(value))
            return " ".join(text_parts)
        elif isinstance(content, list):
            return " ".join([str(item) for item in content])
        else:
            return str(content)
    
    def create_embeddings(self) -> None:
        """Create embeddings for all content"""
        logger.info("Processing course slides...")
        slide_documents = self.process_course_slides()
        
        logger.info("Processing exercises...")
        exercise_documents = self.process_exercises()
        
        all_documents = slide_documents + exercise_documents
        logger.info(f"Total documents to embed: {len(all_documents)}")
        
        # Create embeddings in batches
        batch_size = 32
        for i in tqdm(range(0, len(all_documents), batch_size), desc="Creating embeddings"):
            batch = all_documents[i:i + batch_size]
            
            texts = [doc["text"] for doc in batch]
            embeddings = self.model.encode(texts, show_progress_bar=False)
            
            # Prepare data for ChromaDB
            ids = [doc["id"] for doc in batch]
            metadatas = [doc["metadata"] for doc in batch]
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
        
        # Save embedding statistics
        stats = {
            "total_documents": len(all_documents),
            "course_slides": len(slide_documents),
            "exercises": len(exercise_documents),
            "model_used": self.model.get_sentence_embedding_dimension(),
            "created_at": datetime.now().isoformat()
        }
        
        stats_path = self.base_path / "embeddings" / "embedding_stats.json"
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Embeddings created successfully! Stats saved to {stats_path}")

def main():
    base_path = "/Users/dibakarroysarkar/Desktop/PhDThesis/Teaching Assistant/statics_mechanics_ta"
    embedder = CourseContentEmbedder(base_path)
    embedder.create_embeddings()

if __name__ == "__main__":
    main()
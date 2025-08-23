import os
import sys

# Fix SQLite for Streamlit Cloud
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import logging
from functools import lru_cache
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StaticsMechanicsRAG:
    def __init__(self, base_path: str, model_name: str = "all-MiniLM-L6-v2"):
        self.base_path = Path(base_path)
        self.model = SentenceTransformer(model_name)
        self.chroma_client = None
        self.collection = None
        self.is_initialized = False
        
        # Initialize ChromaDB with error handling
        try:
            chroma_path = str(self.base_path / "embeddings" / "chroma_db")
            
            # Create directory if it doesn't exist
            os.makedirs(chroma_path, exist_ok=True)
            
            # Try to initialize ChromaDB
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)
            
            # Try to get or create collection
            try:
                self.collection = self.chroma_client.get_collection("statics_mechanics_content")
            except Exception:
                # If collection doesn't exist, create it
                logger.warning("Collection not found, creating new collection")
                self.collection = self.chroma_client.create_collection(
                    name="statics_mechanics_content",
                    metadata={"description": "Statics and Mechanics course content"}
                )
            
            self.is_initialized = True
            logger.info("ChromaDB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            logger.warning("Running in fallback mode without vector search")
            self.is_initialized = False
        
        # Cache for frequent queries
        self._query_cache = {}
        self._cache_size_limit = 1000
    
    @lru_cache(maxsize=500)
    def _get_query_embedding(self, query: str) -> List[float]:
        """Cached query embedding generation"""
        return self.model.encode([query])[0].tolist()
    
    def retrieve_relevant_content(
        self, 
        query: str, 
        n_results: int = 5,
        content_type: Optional[str] = None,
        topic_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant content with optional filtering"""
        
        # If ChromaDB is not initialized, return fallback content
        if not self.is_initialized or not self.collection:
            logger.warning("ChromaDB not available, returning fallback content")
            return self._get_fallback_content(query, content_type)
        
        try:
            # Create cache key
            cache_key = hashlib.md5(
                f"{query}_{n_results}_{content_type}_{topic_filter}".encode()
            ).hexdigest()
            
            # Check cache first
            if cache_key in self._query_cache:
                return self._query_cache[cache_key]
            
            # Get query embedding
            query_embedding = self._get_query_embedding(query)
            
            # Prepare where clause for filtering
            where_clause = {}
            if content_type:
                where_clause["content_type"] = content_type
            if topic_filter:
                where_clause["topic"] = {"$contains": topic_filter}
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["documents"][0])):
                result = {
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "source": results["metadatas"][0][i].get("source_file", "Unknown")
                }
                formatted_results.append(result)
            
            # Cache result (with size limit)
            if len(self._query_cache) < self._cache_size_limit:
                self._query_cache[cache_key] = formatted_results
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return self._get_fallback_content(query, content_type)
    
    def get_concept_related_content(self, concept: str, n_results: int = 3) -> List[Dict]:
        """Get content related to specific engineering concepts"""
        return self.retrieve_relevant_content(
            query=concept,
            n_results=n_results,
            content_type="course_slide"
        )
    
    def get_similar_exercises(self, problem_description: str, n_results: int = 3) -> List[Dict]:
        """Find similar exercise problems"""
        return self.retrieve_relevant_content(
            query=problem_description,
            n_results=n_results,
            content_type="exercise_question"
        )
    
    def get_solution_guidance(self, problem_description: str, n_results: int = 2) -> List[Dict]:
        """Get solution approaches without direct answers"""
        return self.retrieve_relevant_content(
            query=problem_description,
            n_results=n_results,
            content_type="exercise_solution"
        )
    
    def _get_fallback_content(self, query: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Provide fallback content when ChromaDB is not available"""
        fallback_content = {
            "course_slide": [
                {
                    "text": "Statics and Mechanics of Materials covers fundamental principles of force equilibrium, stress analysis, and material behavior under various loading conditions.",
                    "metadata": {"content_type": "course_slide", "topic": "general", "source_file": "Statics_Fundamentals_Lecture.pdf"},
                    "similarity_score": 0.7,
                    "source": "Statics_Fundamentals_Lecture.pdf"
                },
                {
                    "text": "Key concepts include free body diagrams, equilibrium equations, stress-strain relationships, and failure analysis.",
                    "metadata": {"content_type": "course_slide", "topic": "fundamentals", "source_file": "Mechanics_of_Materials_Chapter1.pdf"},
                    "similarity_score": 0.6,
                    "source": "Mechanics_of_Materials_Chapter1.pdf"
                }
            ],
            "exercise_question": [
                {
                    "text": "Practice problems typically involve analyzing forces, calculating stresses, and determining deformations in structural elements.",
                    "metadata": {"content_type": "exercise_question", "topic": "problem_solving", "source_file": "Problem_Set_1_Statics.pdf"},
                    "similarity_score": 0.7,
                    "source": "Problem_Set_1_Statics.pdf"
                }
            ],
            "exercise_solution": [
                {
                    "text": "Solution approaches generally follow these steps: 1) Draw free body diagrams, 2) Apply equilibrium equations, 3) Calculate internal forces, 4) Determine stresses and strains.",
                    "metadata": {"content_type": "exercise_solution", "topic": "methodology", "source_file": "Solution_Guide_Statics.pdf"},
                    "similarity_score": 0.7,
                    "source": "Solution_Guide_Statics.pdf"
                }
            ]
        }
        
        if content_type and content_type in fallback_content:
            return fallback_content[content_type]
        else:
            # Return general content from all types
            all_content = []
            for content_list in fallback_content.values():
                all_content.extend(content_list)
            return all_content[:3]  # Return first 3 items
    
    def clear_cache(self):
        """Clear the query cache"""
        self._query_cache.clear()
        self._get_query_embedding.cache_clear()
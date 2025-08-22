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
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.base_path / "embeddings" / "chroma_db")
        )
        self.collection = self.chroma_client.get_collection("statics_mechanics_content")
        
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
    
    def clear_cache(self):
        """Clear the query cache"""
        self._query_cache.clear()
        self._get_query_embedding.cache_clear()
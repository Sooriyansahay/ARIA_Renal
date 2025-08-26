import os
import sys
import pickle
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import logging
from functools import lru_cache
import hashlib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StaticsMechanicsRAG:
    def __init__(self, base_path: str, model_name: str = "all-MiniLM-L6-v2"):
        self.base_path = Path(base_path)
        self.model = None
        self.embeddings_data = None
        self.is_initialized = False
        
        # Initialize SentenceTransformer with proper device handling
        self._initialize_model(model_name)
        
        # Initialize pickle-based storage with error handling
        try:
            embeddings_path = self.base_path / "embeddings"
            pickle_file = embeddings_path / "embeddings_data.pkl"
            
            # Try to load existing embeddings data
            if pickle_file.exists():
                with open(pickle_file, 'rb') as f:
                    self.embeddings_data = pickle.load(f)
                logger.info(f"Loaded {len(self.embeddings_data.get('documents', []))} documents from pickle storage")
            else:
                # Create empty structure if no data exists
                logger.warning("No embeddings data found, creating empty structure")
                self.embeddings_data = {
                    'documents': [],
                    'embeddings': [],
                    'metadatas': [],
                    'ids': []
                }
            
            self.is_initialized = True
            logger.info("Pickle-based storage initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize pickle storage: {e}")
            logger.warning("Running in fallback mode without vector search")
            self.is_initialized = False
            self.embeddings_data = {
                'documents': [],
                'embeddings': [],
                'metadatas': [],
                'ids': []
            }
        
        # Cache for frequent queries
        self._query_cache = {}
        self._cache_size_limit = 1000
    
    def _initialize_model(self, model_name: str):
        """Initialize SentenceTransformer model with proper device handling and error recovery"""
        try:
            # Check if CUDA is available and set device
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Initializing SentenceTransformer on device: {device}")
            
            # Initialize model with device specification
            self.model = SentenceTransformer(model_name, device=device)
            
            # Handle potential meta tensor issues
            if hasattr(self.model, '_modules'):
                for name, module in self.model._modules.items():
                    if module is not None and hasattr(module, 'to'):
                        try:
                            # Use to_empty() for meta tensors, regular to() for others
                            if hasattr(module, 'weight') and module.weight.is_meta:
                                logger.info(f"Using to_empty() for meta tensor in module: {name}")
                                module = module.to_empty(device=device)
                            else:
                                module = module.to(device)
                        except Exception as e:
                            logger.warning(f"Could not move module {name} to device {device}: {e}")
                            # Fallback: try to_empty() if regular to() fails
                            try:
                                module = module.to_empty(device=device)
                                logger.info(f"Successfully used to_empty() for module: {name}")
                            except Exception as e2:
                                logger.error(f"Failed to move module {name} with to_empty(): {e2}")
            
            logger.info("SentenceTransformer model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SentenceTransformer model: {e}")
            logger.warning("Attempting fallback initialization...")
            
            # Fallback: try CPU-only initialization
            try:
                self.model = SentenceTransformer(model_name, device='cpu')
                logger.info("Fallback CPU initialization successful")
            except Exception as e2:
                logger.error(f"Fallback initialization also failed: {e2}")
                logger.warning("Model initialization failed completely - will use fallback content only")
                self.model = None
    
    @lru_cache(maxsize=500)
    def _get_query_embedding(self, query: str) -> List[float]:
        """Cached query embedding generation with error handling"""
        if self.model is None:
            logger.warning("Model not available, returning dummy embedding")
            # Return a dummy embedding vector of appropriate size
            return [0.0] * 384  # all-MiniLM-L6-v2 has 384 dimensions
        
        try:
            return self.model.encode([query])[0].tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return dummy embedding as fallback
            return [0.0] * 384
    
    def retrieve_relevant_content(
        self, 
        query: str, 
        n_results: int = 5,
        content_type: Optional[str] = None,
        topic_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant content with optional filtering"""
        
        # If storage is not initialized, no data, or model is not available, return fallback content
        if (not self.is_initialized or 
            not self.embeddings_data or 
            len(self.embeddings_data.get('documents', [])) == 0 or 
            self.model is None):
            logger.warning("Vector storage or model not available, returning fallback content")
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
            
            # Filter documents based on criteria
            filtered_indices = []
            for i, metadata in enumerate(self.embeddings_data['metadatas']):
                include = True
                if content_type and metadata.get('content_type') != content_type:
                    include = False
                if topic_filter and topic_filter not in metadata.get('topic', ''):
                    include = False
                if include:
                    filtered_indices.append(i)
            
            # If no documents match filters, use all documents
            if not filtered_indices:
                filtered_indices = list(range(len(self.embeddings_data['documents'])))
            
            # Calculate similarities for filtered documents
            if len(filtered_indices) == 0:
                return self._get_fallback_content(query, content_type)
            
            # Get embeddings for filtered documents
            filtered_embeddings = [self.embeddings_data['embeddings'][i] for i in filtered_indices]
            
            # Calculate cosine similarities
            similarities = cosine_similarity([query_embedding], filtered_embeddings)[0]
            
            # Get top n_results
            top_indices = np.argsort(similarities)[::-1][:n_results]
            
            # Format results
            formatted_results = []
            for idx in top_indices:
                original_idx = filtered_indices[idx]
                result = {
                    "text": self.embeddings_data['documents'][original_idx],
                    "metadata": self.embeddings_data['metadatas'][original_idx],
                    "similarity_score": float(similarities[idx]),
                    "source": self.embeddings_data['metadatas'][original_idx].get("source_file", "Unknown")
                }
                formatted_results.append(result)
            
            # Cache result (with size limit)
            if len(self._query_cache) < self._cache_size_limit:
                self._query_cache[cache_key] = formatted_results
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying vector storage: {e}")
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
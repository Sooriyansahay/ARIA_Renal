from openai import OpenAI
from typing import List, Dict, Any
import json
from pathlib import Path
import os
from .embedding.rag_retriever import StaticsMechanicsRAG
from .database.conversation_storage import conversation_storage
import logging
from datetime import datetime
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StaticsMechanicsTA:
    def __init__(self, base_path: str, api_key: str):
        self.base_path = Path(base_path)
        self.rag = StaticsMechanicsRAG(base_path)
        self.client = OpenAI(api_key=api_key)
        self.session_id = str(uuid.uuid4())  # Generate unique session ID
        
        # Teaching philosophy prompts
        self.system_prompt = """
You are a Teaching Assistant for Statics & Mechanics of Materials. Your role is to GUIDE students through problem-solving steps, NOT to give direct answers.

CORE PRINCIPLES:
1. NEVER provide direct numerical answers
2. ALWAYS break down problems into logical steps
3. Ask guiding questions to help students think
4. Provide relevant formulas and concepts when needed
5. Use analogies and examples to clarify concepts
6. Encourage students to attempt each step themselves
7. Point out common mistakes and how to avoid them

When a student asks a question:
1. Identify the key concepts involved
2. Break the problem into manageable steps
3. Guide them through the approach without solving
4. Provide hints and ask questions to check understanding
5. Reference relevant course material when helpful

Remember: Your goal is to help students LEARN, not to do their work for them.
"""
    
    def generate_response(
        self, 
        student_question: str, 
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate a teaching-focused response"""
        
        start_time = datetime.now()
        
        try:
            # Retrieve relevant content
            relevant_content = self._get_relevant_content(student_question)
            
            # Prepare context for GPT
            context = self._prepare_context(relevant_content)
            
            # Create messages for GPT
            messages = self._create_messages(
                student_question, 
                context, 
                conversation_history
            )
            
            # Generate response with GPT using new client format
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=800,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            assistant_response = response.choices[0].message.content
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Log the interaction to Supabase
            self._log_interaction(
                student_question, 
                assistant_response, 
                relevant_content, 
                response_time
            )
            
            return {
                "response": assistant_response,
                "relevant_topics": [content["metadata"].get("topic", "Unknown") for content in relevant_content],
                "concepts_covered": self._extract_concepts_from_content(relevant_content),
                "suggested_review": self._suggest_review_materials(relevant_content)
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "I'm having trouble processing your question right now. Could you please rephrase it or break it down into smaller parts?",
                "error": str(e)
            }
    
    def _get_relevant_content(self, question: str) -> List[Dict]:
        """Retrieve relevant content based on question type"""
        
        # Get concept-related content
        concept_content = self.rag.get_concept_related_content(question, n_results=2)
        
        # Get similar exercises
        exercise_content = self.rag.get_similar_exercises(question, n_results=2)
        
        # Get solution guidance (but we'll use this carefully)
        solution_content = self.rag.get_solution_guidance(question, n_results=1)
        
        # Combine and deduplicate
        all_content = concept_content + exercise_content + solution_content
        
        # Remove duplicates based on content similarity
        unique_content = self._deduplicate_content(all_content)
        
        return unique_content[:5]  # Limit to top 5 most relevant
    
    def _prepare_context(self, relevant_content: List[Dict]) -> str:
        """Prepare context from retrieved content"""
        context_parts = []
        
        for content in relevant_content:
            content_type = content["metadata"].get("content_type", "unknown")
            topic = content["metadata"].get("topic", "Unknown Topic")
            
            context_part = f"\n--- {content_type.upper()}: {topic} ---\n"
            context_part += content["text"]
            
            # Add concepts and formulas if available
            if "concepts" in content["metadata"]:
                concepts = content["metadata"]["concepts"]
                if concepts:
                    context_part += f"\nKey Concepts: {', '.join(concepts)}"
            
            if "formulas" in content["metadata"]:
                formulas = content["metadata"]["formulas"]
                if formulas:
                    context_part += f"\nRelevant Formulas: {'; '.join(formulas[:2])}"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _create_messages(
        self, 
        question: str, 
        context: str, 
        conversation_history: List[Dict] = None
    ) -> List[Dict]:
        """Create message structure for GPT"""
        
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                messages.append(msg)
        
        # Add current question with context
        user_message = f"""
Student Question: {question}

Relevant Course Material:
{context}

Please provide step-by-step guidance to help the student solve this problem. Do NOT give direct answers. Focus on:
1. Breaking down the problem
2. Identifying key concepts
3. Suggesting the approach
4. Asking guiding questions
5. Providing hints when needed
"""
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _deduplicate_content(self, content_list: List[Dict]) -> List[Dict]:
        """Remove duplicate content based on text similarity"""
        unique_content = []
        seen_texts = set()
        
        for content in content_list:
            # Create a simple hash of the text for deduplication
            text_hash = hash(content["text"][:200])  # First 200 chars
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_content.append(content)
        
        return unique_content
    
    def _extract_concepts_from_content(self, content_list: List[Dict]) -> List[str]:
        """Extract unique concepts from retrieved content"""
        concepts = set()
        for content in content_list:
            if "concepts" in content["metadata"]:
                concepts.update(content["metadata"]["concepts"])
        return list(concepts)
    
    def _suggest_review_materials(self, content_list: List[Dict]) -> List[str]:
        """Suggest review materials based on retrieved content"""
        topics = set()
        for content in content_list:
            topic = content["metadata"].get("topic", "")
            if topic:
                topics.add(topic)
        return list(topics)
    
    def _log_interaction(self, question: str, response: str, context: List[Dict], response_time: float = None):
        """Log interactions to Supabase database for analytics and improvement"""
        try:
            context_sources = [c["metadata"].get("source_file", "unknown") for c in context]
            concepts_used = self._extract_concepts_from_content(context)
            
            # Store conversation in Supabase
            success = conversation_storage.store_conversation(
                session_id=self.session_id,
                user_question=question,
                ta_response=response,
                context_sources=context_sources,
                concepts_used=concepts_used,
                response_time=response_time
            )
            
            if success:
                logger.info("Conversation logged to Supabase successfully")
            else:
                logger.warning("Failed to log conversation to Supabase, falling back to local logging")
                self._fallback_log_interaction(question, response, context, response_time)
                
        except Exception as e:
            logger.error(f"Error logging to Supabase: {e}")
            # Fallback to local JSON logging if Supabase fails
            self._fallback_log_interaction(question, response, context, response_time)
    
    def _fallback_log_interaction(self, question: str, response: str, context: List[Dict], response_time: float = None):
        """Fallback logging method using JSON files"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "question": question,
                "response_length": len(response),
                "context_sources": [c["metadata"].get("source_file", "unknown") for c in context],
                "concepts_used": self._extract_concepts_from_content(context),
                "response_time": response_time
            }
            
            log_file = self.base_path / "logs" / "ta_interactions.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
                
            logger.info("Conversation logged to local file as fallback")
            
        except Exception as e:
            logger.error(f"Failed to log conversation even to local file: {e}")
    
    def get_session_id(self) -> str:
        """Get the current session ID"""
        return self.session_id
    
    def new_session(self) -> str:
        """Start a new session and return the new session ID"""
        self.session_id = str(uuid.uuid4())
        logger.info(f"Started new session: {self.session_id}")
        return self.session_id
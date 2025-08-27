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
        
        # Concise teaching philosophy prompts for direct responses
        self.system_prompt = """
You are ARIA, a Teaching Assistant for Statics & Mechanics of Materials. Your role is to provide CONCISE, DIRECT guidance that efficiently addresses student questions.

CORE PRINCIPLES:
1. Give clear, straightforward answers
2. Focus on essential concepts and key steps
3. Provide relevant formulas when needed
4. Keep responses brief but complete
5. Use simple, direct language
6. Include source references
7. Ask one focused follow-up question when helpful

RESPONSE FORMAT:
- Start with the key concept or answer
- Provide essential steps or formula
- Give brief practical context if relevant
- End with a focused question or next step

Remember: Your goal is to help students learn efficiently with clear, direct guidance that addresses their specific question without overwhelming detail.
"""
    
    def generate_response(
        self, 
        student_question: str, 
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate a teaching-focused response"""
        
        start_time = datetime.now()
        
        try:
            # Check if question is relevant to course materials
            is_course_relevant = self._is_question_course_relevant(student_question)
            logger.info(f"Question relevance to course materials: {is_course_relevant}")
            
            if is_course_relevant:
                # For course-relevant questions: retrieve content and use course context
                relevant_content = self._get_relevant_content(student_question)
                context = self._prepare_context(relevant_content)
                messages = self._create_messages(
                    student_question, 
                    context, 
                    conversation_history
                )
            else:
                # For irrelevant questions: use general assistant mode without course context
                relevant_content = []  # No course content for irrelevant questions
                messages = self._create_general_messages(
                    student_question,
                    conversation_history
                )
            
            # Generate response with GPT-4 using parameters optimized for concise responses
            response = self.client.chat.completions.create(
                model="gpt-4", 
                messages=messages,
                max_tokens=600,  # Reduced for concise responses
                temperature=0.5,  # Balanced temperature for clear, direct responses
                presence_penalty=0.1,  # Light penalty to encourage focused answers
                frequency_penalty=0.1,  # Light penalty to avoid repetition
                top_p=0.9  # Slightly reduced for more focused responses
            )
            
            assistant_response = response.choices[0].message.content
            logger.info(f"Generated answer length: {len(assistant_response)}")
            
            # Only add source references if question is relevant to course materials
            if is_course_relevant and relevant_content:
                source_references = self._format_source_references(relevant_content)
                logger.info(f"Source references: {source_references}")
                
                if source_references:
                    assistant_response += f"\n\n📚 Sources: {source_references}"
                    logger.info(f"Final answer with sources: {assistant_response[-100:]}...")
            else:
                logger.info("Question not course-relevant or no content found, skipping source references")
            
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
                "relevant_topics": [content["metadata"].get("topic", "Unknown") for content in relevant_content] if relevant_content else [],
                "concepts_covered": self._extract_concepts_from_content(relevant_content) if relevant_content else [],
                "suggested_review": self._suggest_review_materials(relevant_content) if relevant_content else [],
                "is_course_relevant": is_course_relevant,
                "context_sources": [c["metadata"].get("source_file", "unknown") for c in relevant_content] if relevant_content else []
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
        
        # Get solution guidance
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
            
            # Add essential metadata information
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

Provide CONCISE guidance (3-5 sentences max). Focus on:
1. Identify ONE key concept
2. Suggest a 2-3 step approach
3. Ask ONE guiding question

Do NOT give direct answers. Keep it brief and focused.
"""
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _create_general_messages(
        self, 
        question: str, 
        conversation_history: List[Dict] = None
    ) -> List[Dict]:
        """Create message structure for general (non-course) questions"""
        
        # Use a general assistant system prompt for non-course questions
        general_system_prompt = """
You are ARIA, a helpful teaching assistant. The user has asked a question that is not related to statics and mechanics of materials coursework.

Provide a helpful, concise response to their question. Be friendly and informative, but keep your response brief (3-5 sentences). 

If the question is completely unrelated to academics, gently redirect them back to course-related topics while still being helpful.
"""
        
        messages = [
            {"role": "system", "content": general_system_prompt}
        ]
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                messages.append(msg)
        
        # Add current question without course context
        messages.append({"role": "user", "content": question})
        
        return messages
    
    def _deduplicate_content(self, content_list: List[Dict]) -> List[Dict]:
        """Remove duplicate content based on text similarity"""
        unique_content = []
        seen_texts = set()
        
        for content in content_list:
            # Create a simple hash of the text for deduplication
            text_hash = hash(content["text"][:300])  # Increased for better deduplication
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_content.append(content)
        
        return unique_content
    
    def _format_source_references(self, content_list: List[Dict]) -> str:
        """Format source references from retrieved content"""
        sources = set()
        
        # Debug logging
        logger.info(f"Formatting sources for {len(content_list)} content items")
        
        for i, content in enumerate(content_list):
            metadata = content.get("metadata", {})
            logger.info(f"Content {i} metadata keys: {list(metadata.keys())}")
            
            # Try multiple possible source field names
            source_file = (
                metadata.get("source_file") or 
                metadata.get("source") or 
                metadata.get("filename") or 
                metadata.get("file_name") or
                content.get("source", "")
            )
            
            logger.info(f"Content {i} source_file: {source_file}")
            
            if source_file:
                # Extract just the filename from the full path
                import os
                filename = os.path.basename(source_file)
                
                # Clean up the source file name for better readability
                clean_source = filename.replace(".json", "").replace(".pdf", "").replace("_", " ").replace("-", " ")
                
                # Convert to title case and clean up specific patterns
                clean_source = clean_source.title()
                
                # Handle specific course material patterns
                if "Beams Bending Members" in clean_source:
                    clean_source = "Beams: Flexural Stresses and Strains"
                elif "Axial Force Members" in clean_source:
                    clean_source = "Axial Loading: Stress and Strain"
                elif "Torsion Members" in clean_source:
                    clean_source = "Torsion: Shear Stress and Angle of Twist"
                elif "Extracted" in clean_source:
                    # Remove "Extracted" suffix and clean up
                    clean_source = clean_source.replace(" Extracted", "")
                    
                sources.add(clean_source)
            else:
                # Fallback: try to extract from topic or content_type
                topic = metadata.get("topic", "")
                content_type = metadata.get("content_type", "")
                if topic:
                    sources.add(f"{content_type.title()}: {topic}")
        
        result = ", ".join(sorted(sources)) if sources else "Course Materials"
        logger.info(f"Final formatted sources: {result}")
        return result
    
    def _extract_concepts_from_content(self, content_list: List[Dict]) -> List[str]:
        """Extract unique concepts from retrieved content"""
        concepts = set()
        for content in content_list:
            if "concepts" in content["metadata"]:
                concepts.update(content["metadata"]["concepts"])
        return list(concepts)
    
    def _is_question_course_relevant(self, question: str) -> bool:
        """Check if the question is relevant to statics and mechanics course materials"""
        
        # Convert question to lowercase for case-insensitive matching
        question_lower = question.lower()
        
        # Define course-relevant keywords
        statics_keywords = [
            'static', 'statics', 'equilibrium', 'force', 'forces', 'moment', 'moments',
            'torque', 'reaction', 'reactions', 'support', 'supports', 'free body diagram',
            'fbd', 'beam', 'beams', 'truss', 'trusses', 'frame', 'frames', 'joint',
            'joints', 'pin', 'roller', 'fixed', 'cantilever'
        ]
        
        mechanics_keywords = [
            'stress', 'strain', 'deformation', 'deflection', 'bending', 'shear',
            'tension', 'compression', 'torsion', 'axial', 'flexural', 'elastic',
            'modulus', 'material', 'materials', 'mechanics', 'strength', 'loading',
            'load', 'loads', 'pressure', 'normal', 'tangential', 'principal',
            'mohr', 'circle', 'yield', 'failure', 'safety', 'factor'
        ]
        
        engineering_keywords = [
            'engineering', 'structural', 'mechanical', 'civil', 'design',
            'analysis', 'calculate', 'calculation', 'solve', 'problem',
            'diagram', 'section', 'cross-section', 'area', 'inertia',
            'centroid', 'geometry', 'coordinate', 'axis', 'axes'
        ]
        
        # Combine all keywords
        all_keywords = statics_keywords + mechanics_keywords + engineering_keywords
        
        # Check if any keyword is present in the question
        for keyword in all_keywords:
            if keyword in question_lower:
                return True
        
        # Additional check for common engineering units and symbols
        engineering_units = [
            'kn', 'kip', 'lb', 'lbs', 'newton', 'newtons', 'n', 'pa', 'psi',
            'mpa', 'gpa', 'kpa', 'mm', 'cm', 'm', 'ft', 'in', 'inch', 'inches',
            'degree', 'degrees', 'radian', 'radians', 'kg', 'gram', 'ton'
        ]
        
        for unit in engineering_units:
            if unit in question_lower:
                return True
        
        # Check for mathematical expressions common in engineering
        math_patterns = ['σ', 'τ', 'ε', 'δ', 'θ', 'φ', 'ω', 'α', 'β', 'γ']
        for pattern in math_patterns:
            if pattern in question:
                return True
        
        return False
    
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
                
            logger.info("Conversation logged to local file successfully")
            
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
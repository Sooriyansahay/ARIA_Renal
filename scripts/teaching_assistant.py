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
        
        # Enhanced teaching philosophy prompts for comprehensive responses
        self.system_prompt = """
You are ARIA, an advanced Teaching Assistant for Statics & Mechanics of Materials. Your role is to provide COMPREHENSIVE, DETAILED guidance that thoroughly explains concepts while maintaining pedagogical excellence.

CORE PRINCIPLES:
1. Provide thorough explanations with multiple approaches and perspectives
2. Include detailed step-by-step reasoning and methodology
3. Explain the underlying physics and mathematical principles
4. Connect concepts to real-world applications and engineering practice
5. Offer multiple solution strategies when applicable
6. Provide comprehensive background theory and context
7. Include relevant formulas with detailed explanations of each variable
8. Always include source references and suggest additional resources
9. Use clear, detailed language with technical precision
10. Encourage deep understanding through comprehensive analysis

RESPONSE FORMAT:
- Begin with a comprehensive overview of the relevant concepts
- Provide detailed theoretical background and fundamental principles
- Explain multiple approaches to problem-solving with full reasoning
- Include step-by-step methodology with explanations for each step
- Discuss practical applications and engineering significance
- Provide comprehensive formula derivations and variable explanations
- Suggest related topics for deeper understanding
- End with thought-provoking questions that encourage further exploration
- Include comprehensive references and additional learning resources

Remember: Your goal is to foster DEEP, COMPREHENSIVE understanding through detailed explanations and thorough analysis. Provide rich, educational content that goes beyond surface-level guidance.
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
            
            # Generate response with GPT-4o using enhanced parameters for comprehensive responses
            response = self.client.chat.completions.create(
                model="gpt-4", 
                messages=messages,
                max_tokens=2000,  # Increased for comprehensive responses
                temperature=0.3,  # Lower temperature for more focused, detailed responses
                presence_penalty=0.0,  # Reduced to allow comprehensive coverage
                frequency_penalty=0.0,  # Reduced to allow thorough explanations
                top_p=0.95  # Added for better response quality
            )
            
            assistant_response = response.choices[0].message.content
            logger.info(f"Generated answer length: {len(assistant_response)}")
            
            # Only add source references if question is relevant to course materials
            if is_course_relevant and relevant_content:
                source_references = self._format_source_references(relevant_content)
                logger.info(f"Source references: {source_references}")
                
                if source_references:
                    assistant_response += f"\n\n📚 **Comprehensive Sources and References:**\n{source_references}"
                    
                    # Add additional learning resources
                    additional_resources = self._generate_additional_resources(relevant_content)
                    if additional_resources:
                        assistant_response += f"\n\n📖 **Recommended Additional Study Materials:**\n{additional_resources}"
                    
                    logger.info(f"Final answer with comprehensive sources: {assistant_response[-200:]}...")
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
                "context_sources": [c["metadata"].get("source_file", "unknown") for c in relevant_content] if relevant_content else [],
                "comprehensive_analysis": True,
                "response_depth": "comprehensive"
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "I'm experiencing technical difficulties processing your question. Let me provide a comprehensive alternative approach: Could you please rephrase your question or break it down into specific components? This will help me provide you with the detailed, thorough analysis you deserve. I'm designed to offer comprehensive explanations covering theoretical foundations, practical applications, and multiple solution approaches.",
                "error": str(e)
            }
    
    def _get_relevant_content(self, question: str) -> List[Dict]:
        """Retrieve comprehensive relevant content based on question type"""
        
        # Get concept-related content (increased for comprehensive coverage)
        concept_content = self.rag.get_concept_related_content(question, n_results=4)
        
        # Get similar exercises (increased for comprehensive examples)
        exercise_content = self.rag.get_similar_exercises(question, n_results=3)
        
        # Get solution guidance (increased for comprehensive methodology)
        solution_content = self.rag.get_solution_guidance(question, n_results=2)
        
        # Combine and deduplicate
        all_content = concept_content + exercise_content + solution_content
        
        # Remove duplicates based on content similarity
        unique_content = self._deduplicate_content(all_content)
        
        return unique_content[:8]  # Increased limit for comprehensive coverage
    
    def _prepare_context(self, relevant_content: List[Dict]) -> str:
        """Prepare comprehensive context from retrieved content"""
        context_parts = []
        
        for content in relevant_content:
            content_type = content["metadata"].get("content_type", "unknown")
            topic = content["metadata"].get("topic", "Unknown Topic")
            
            context_part = f"\n--- {content_type.upper()}: {topic} ---\n"
            context_part += content["text"]
            
            # Add comprehensive metadata information
            if "concepts" in content["metadata"]:
                concepts = content["metadata"]["concepts"]
                if concepts:
                    context_part += f"\n\n**Key Concepts:** {', '.join(concepts)}"
            
            if "formulas" in content["metadata"]:
                formulas = content["metadata"]["formulas"]
                if formulas:
                    context_part += f"\n\n**Relevant Formulas:** {'; '.join(formulas)}"
            
            if "applications" in content["metadata"]:
                applications = content["metadata"]["applications"]
                if applications:
                    context_part += f"\n\n**Practical Applications:** {'; '.join(applications)}"
            
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
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
        
        # Add conversation history if available (increased context window)
        if conversation_history:
            for msg in conversation_history[-10:]:  # Increased for better context
                messages.append(msg)
        
        # Add current question with comprehensive context
        user_message = f"""
Student Question: {question}

Comprehensive Course Material and Context:
{context}

Provide a COMPREHENSIVE, DETAILED response that includes:

1. **Theoretical Foundation**: Explain the underlying principles and theory in detail
2. **Multiple Approaches**: Present different methods and perspectives for addressing this topic
3. **Step-by-Step Analysis**: Provide detailed methodology with explanations for each step
4. **Mathematical Framework**: Include relevant formulas with comprehensive variable explanations
5. **Practical Applications**: Discuss real-world engineering applications and significance
6. **Conceptual Connections**: Link to related topics and broader engineering principles
7. **Problem-Solving Strategies**: Offer comprehensive approaches for similar problems
8. **Critical Thinking**: Encourage deeper analysis with thought-provoking questions
9. **Additional Resources**: Suggest related topics for further comprehensive study

Ensure your response is thorough, educational, and promotes deep understanding through comprehensive analysis and detailed explanations.
"""
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _create_general_messages(
        self, 
        question: str, 
        conversation_history: List[Dict] = None
    ) -> List[Dict]:
        """Create message structure for general (non-course) questions"""
        
        # Enhanced general assistant system prompt for comprehensive responses
        general_system_prompt = """
You are ARIA, an advanced teaching assistant with expertise across multiple disciplines. The user has asked a question that may not be directly related to statics and mechanics of materials coursework.

Provide a comprehensive, detailed response that:
1. Thoroughly addresses their question with multiple perspectives
2. Includes relevant background information and context
3. Offers practical applications and real-world connections
4. Suggests related topics for further exploration
5. Maintains an educational and supportive tone
6. Provides detailed explanations and reasoning

If the question is completely unrelated to academics, provide helpful information while gently suggesting how it might connect to engineering or academic topics, and offer to help with course-related questions for more comprehensive assistance.
"""
        
        messages = [
            {"role": "system", "content": general_system_prompt}
        ]
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-10:]:  # Increased context window
                messages.append(msg)
        
        # Add current question without course context but with comprehensive instruction
        enhanced_question = f"""
{question}

Please provide a comprehensive, detailed response that thoroughly addresses this question with multiple perspectives, relevant background information, and practical applications where applicable.
"""
        
        messages.append({"role": "user", "content": enhanced_question})
        
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
        
        # Create comprehensive source listing
        detailed_sources = []
        for source in sorted(sources):
            detailed_sources.append(f"• {source}")
        
        result = "\n".join(detailed_sources) if detailed_sources else "• Course Materials - Comprehensive Coverage"
        logger.info(f"Final comprehensive sources: {result}")
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
        """Suggest comprehensive review materials based on retrieved content"""
        topics = set()
        concepts = set()
        
        for content in content_list:
            topic = content["metadata"].get("topic", "")
            if topic:
                topics.add(topic)
            
            if "concepts" in content["metadata"]:
                concepts.update(content["metadata"]["concepts"])
        
        # Combine topics and concepts for comprehensive review suggestions
        review_materials = list(topics) + [f"Concept: {concept}" for concept in list(concepts)[:3]]
        
        return review_materials[:8]  # Increased for comprehensive coverage
    
    def _generate_additional_resources(self, content_list: List[Dict]) -> str:
        """Generate additional learning resources based on content"""
        topics = set()
        concepts = set()
        
        for content in content_list:
            metadata = content.get("metadata", {})
            if "topic" in metadata:
                topics.add(metadata["topic"])
            if "concepts" in metadata:
                concepts.update(metadata["concepts"])
        
        resources = []
        
        if topics:
            resources.append(f"• Related Topics: {', '.join(list(topics)[:5])}")
        
        if concepts:
            resources.append(f"• Key Concepts for Further Study: {', '.join(list(concepts)[:5])}")
        
        # Add general recommendations
        resources.extend([
            "• Review fundamental principles and derivations",
            "• Practice with similar problems and variations",
            "• Explore real-world engineering applications",
            "• Connect concepts to broader engineering principles"
        ])
        
        return "\n".join(resources)
    
    def _log_interaction(self, question: str, response: str, context: List[Dict], response_time: float = None):
        """Log interactions to Supabase database for analytics and improvement"""
        try:
            context_sources = [c["metadata"].get("source_file", "unknown") for c in context]
            concepts_used = self._extract_concepts_from_content(context)
            
            # Store conversation in Supabase with enhanced metadata
            success = conversation_storage.store_conversation(
                session_id=self.session_id,
                user_question=question,
                ta_response=response,
                context_sources=context_sources,
                concepts_used=concepts_used,
                response_time=response_time
            )
            
            if success:
                logger.info("Comprehensive conversation logged to Supabase successfully")
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
                "response_time": response_time,
                "response_type": "comprehensive",
                "model_used": "gpt-4"
            }
            
            log_file = self.base_path / "logs" / "ta_interactions.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
                
            logger.info("Comprehensive conversation logged to local file successfully")
            
        except Exception as e:
            logger.error(f"Failed to log conversation even to local file: {e}")
    
    def get_session_id(self) -> str:
        """Get the current session ID"""
        return self.session_id
    
    def new_session(self) -> str:
        """Start a new session and return the new session ID"""
        self.session_id = str(uuid.uuid4())
        logger.info(f"Started new comprehensive session: {self.session_id}")
        return self.session_id
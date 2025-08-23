from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging
import json
from pathlib import Path
from .supabase_config import supabase_config

logger = logging.getLogger(__name__)

class FeedbackStorage:
    """
    Handle feedback storage and retrieval using Supabase or fallback to JSON
    """
    
    def __init__(self):
        self.client = supabase_config.get_client()
        self.table_name = 'feedback'
        self.fallback_file = Path(__file__).parent.parent.parent / "feedback_data.json"
        
    def store_feedback(self, 
                      session_id: str,
                      conversation_id: Optional[str],
                      message_index: int,
                      user_question: str,
                      ai_response: str,
                      feedback_type: str,
                      concepts_covered: List[str] = None,
                      response_time: float = None) -> bool:
        """
        Store feedback data in Supabase database or fallback to JSON
        
        Args:
            session_id: Session identifier
            conversation_id: Related conversation ID (optional)
            message_index: Index of the message in conversation
            user_question: The user's question
            ai_response: The AI's response
            feedback_type: Type of feedback ('helpful', 'not_helpful', 'partially_helpful')
            concepts_covered: List of concepts covered in the response
            response_time: Response time in seconds
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        
        if self.client and supabase_config.is_connected():
            return self._store_in_database(session_id, conversation_id, message_index, 
                                         user_question, ai_response, feedback_type,
                                         concepts_covered, response_time)
        else:
            return self._store_in_json(session_id, conversation_id, message_index,
                                     user_question, ai_response, feedback_type,
                                     concepts_covered, response_time)
    
    def _store_in_database(self, session_id: str, conversation_id: Optional[str],
                          message_index: int, user_question: str, ai_response: str,
                          feedback_type: str, concepts_covered: List[str],
                          response_time: float) -> bool:
        """
        Store feedback in Supabase database
        """
        try:
            feedback_data = {
                'id': str(uuid.uuid4()),
                'session_id': session_id,
                'conversation_id': conversation_id,
                'message_index': message_index,
                'user_question': user_question,
                'ai_response': ai_response,
                'feedback_type': feedback_type,
                'concepts_covered': concepts_covered or [],
                'response_time': response_time
            }
            
            response = self.client.table(self.table_name).insert(feedback_data).execute()
            
            if response.data:
                logger.info(f"Feedback stored successfully with ID: {feedback_data['id']}")
                return True
            else:
                logger.error("Failed to store feedback - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error storing feedback in database: {e}")
            # Fallback to JSON storage
            return self._store_in_json(session_id, conversation_id, message_index,
                                     user_question, ai_response, feedback_type,
                                     concepts_covered, response_time)
    
    def _store_in_json(self, session_id: str, conversation_id: Optional[str],
                      message_index: int, user_question: str, ai_response: str,
                      feedback_type: str, concepts_covered: List[str],
                      response_time: float) -> bool:
        """
        Fallback storage method using JSON files
        """
        try:
            feedback_entry = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'conversation_id': conversation_id,
                'message_index': message_index,
                'user_question': user_question,
                'ai_response': ai_response,
                'feedback_type': feedback_type,
                'concepts_covered': concepts_covered or [],
                'response_time': response_time
            }
            
            # Load existing feedback data
            existing_data = []
            if self.fallback_file.exists():
                try:
                    with open(self.fallback_file, 'r') as f:
                        existing_data = json.load(f)
                except json.JSONDecodeError:
                    logger.warning("Corrupted feedback file, starting fresh")
                    existing_data = []
            
            # Add new feedback
            existing_data.append(feedback_entry)
            
            # Save back to file
            self.fallback_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.fallback_file, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            logger.info(f"Feedback stored in JSON file: {feedback_entry['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing feedback in JSON: {e}")
            return False
    
    def update_feedback(self, session_id: str, message_index: int, 
                       new_feedback_type: str) -> bool:
        """
        Update existing feedback for a specific message
        
        Args:
            session_id: Session identifier
            message_index: Index of the message in conversation
            new_feedback_type: New feedback type
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        
        if self.client and supabase_config.is_connected():
            return self._update_in_database(session_id, message_index, new_feedback_type)
        else:
            return self._update_in_json(session_id, message_index, new_feedback_type)
    
    def _update_in_database(self, session_id: str, message_index: int,
                           new_feedback_type: str) -> bool:
        """
        Update feedback in Supabase database
        """
        try:
            response = self.client.table(self.table_name).update({
                'feedback_type': new_feedback_type,
                'updated_at': datetime.now().isoformat()
            }).eq('session_id', session_id).eq('message_index', message_index).execute()
            
            if response.data:
                logger.info(f"Feedback updated successfully for session {session_id}, message {message_index}")
                return True
            else:
                logger.error("Failed to update feedback - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error updating feedback in database: {e}")
            return self._update_in_json(session_id, message_index, new_feedback_type)
    
    def _update_in_json(self, session_id: str, message_index: int,
                       new_feedback_type: str) -> bool:
        """
        Update feedback in JSON file
        """
        try:
            if not self.fallback_file.exists():
                return False
            
            with open(self.fallback_file, 'r') as f:
                feedback_data = json.load(f)
            
            # Find and update the feedback entry
            updated = False
            for entry in feedback_data:
                if (entry.get('session_id') == session_id and 
                    entry.get('message_index') == message_index):
                    entry['feedback_type'] = new_feedback_type
                    entry['updated_at'] = datetime.now().isoformat()
                    updated = True
                    break
            
            if updated:
                with open(self.fallback_file, 'w') as f:
                    json.dump(feedback_data, f, indent=2, default=str)
                logger.info(f"Feedback updated in JSON for session {session_id}, message {message_index}")
                return True
            else:
                logger.warning(f"Feedback not found for session {session_id}, message {message_index}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating feedback in JSON: {e}")
            return False
    
    def delete_feedback(self, session_id: str, message_index: int) -> bool:
        """
        Delete feedback for a specific message
        
        Args:
            session_id: Session identifier
            message_index: Index of the message in conversation
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        
        if self.client and supabase_config.is_connected():
            return self._delete_in_database(session_id, message_index)
        else:
            return self._delete_in_json(session_id, message_index)
    
    def _delete_in_database(self, session_id: str, message_index: int) -> bool:
        """
        Delete feedback from Supabase database
        """
        try:
            response = self.client.table(self.table_name).delete().eq(
                'session_id', session_id
            ).eq('message_index', message_index).execute()
            
            logger.info(f"Feedback deleted for session {session_id}, message {message_index}")
            return True
                
        except Exception as e:
            logger.error(f"Error deleting feedback from database: {e}")
            return self._delete_in_json(session_id, message_index)
    
    def _delete_in_json(self, session_id: str, message_index: int) -> bool:
        """
        Delete feedback from JSON file
        """
        try:
            if not self.fallback_file.exists():
                return False
            
            with open(self.fallback_file, 'r') as f:
                feedback_data = json.load(f)
            
            # Filter out the feedback entry
            original_length = len(feedback_data)
            feedback_data = [
                entry for entry in feedback_data
                if not (entry.get('session_id') == session_id and 
                       entry.get('message_index') == message_index)
            ]
            
            if len(feedback_data) < original_length:
                with open(self.fallback_file, 'w') as f:
                    json.dump(feedback_data, f, indent=2, default=str)
                logger.info(f"Feedback deleted from JSON for session {session_id}, message {message_index}")
                return True
            else:
                logger.warning(f"Feedback not found for session {session_id}, message {message_index}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting feedback from JSON: {e}")
            return False

# Global instance
feedback_storage = FeedbackStorage()
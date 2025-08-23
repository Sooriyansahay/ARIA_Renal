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
        self.table_name = 'conversations'
        self.fallback_file = Path(__file__).parent.parent.parent / "feedback_data.json"
        
    def update_feedback(self, 
                       conversation_id: str,
                       feedback_type: str) -> bool:
        """
        Update feedback for a specific conversation in Supabase database or fallback to JSON
        
        Args:
            conversation_id: The conversation ID to update
            feedback_type: Type of feedback ('helpful', 'not_helpful', 'partially_helpful')
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        
        if self.client and supabase_config.is_connected():
            return self._update_in_database(conversation_id, feedback_type)
        else:
            return self._update_in_json(conversation_id, feedback_type)
    
    def _update_in_database(self, conversation_id: str, feedback_type: str) -> bool:
        """
        Update feedback in conversations table in Supabase database
        """
        try:
            response = self.client.table(self.table_name).update({
                'feedback': feedback_type
            }).eq('id', conversation_id).execute()
            
            if response.data:
                logger.info(f"Feedback updated successfully for conversation: {conversation_id}")
                return True
            else:
                logger.error("Failed to update feedback - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error updating feedback in database: {e}")
            # Fallback to JSON storage
            return self._update_in_json(conversation_id, feedback_type)
    
    def _update_in_json(self, conversation_id: str, feedback_type: str) -> bool:
        """
        Fallback method to update feedback using JSON files
        """
        try:
            feedback_entry = {
                'conversation_id': conversation_id,
                'feedback_type': feedback_type,
                'timestamp': datetime.now().isoformat()
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
            
            # Update existing feedback or add new one
            updated = False
            for entry in existing_data:
                if entry.get('conversation_id') == conversation_id:
                    entry['feedback_type'] = feedback_type
                    entry['timestamp'] = datetime.now().isoformat()
                    updated = True
                    break
            
            if not updated:
                existing_data.append(feedback_entry)
            
            # Save back to file
            self.fallback_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.fallback_file, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            logger.info(f"Feedback updated in JSON file for conversation: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating feedback in JSON: {e}")
            return False
    
    def get_conversation_feedback(self, conversation_id: str) -> Optional[str]:
        """
        Get feedback for a specific conversation
        
        Args:
            conversation_id: The conversation ID to get feedback for
            
        Returns:
            str: The feedback type if found, None otherwise
        """
        
        if self.client and supabase_config.is_connected():
            return self._get_feedback_from_database(conversation_id)
        else:
            return self._get_feedback_from_json(conversation_id)
    
    def _get_feedback_from_database(self, conversation_id: str) -> Optional[str]:
        """
        Get feedback from conversations table in Supabase database
        """
        try:
            response = self.client.table(self.table_name).select('feedback').eq('id', conversation_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0].get('feedback')
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting feedback from database: {e}")
            return self._get_feedback_from_json(conversation_id)
    
    def _get_feedback_from_json(self, conversation_id: str) -> Optional[str]:
        """
        Get feedback from JSON file
        """
        try:
            if not self.fallback_file.exists():
                return None
            
            with open(self.fallback_file, 'r') as f:
                feedback_data = json.load(f)
            
            # Find the feedback entry
            for entry in feedback_data:
                if entry.get('conversation_id') == conversation_id:
                    return entry.get('feedback_type')
            
            return None
                
        except Exception as e:
            logger.error(f"Error getting feedback from JSON: {e}")
            return None
    
    def clear_conversation_feedback(self, conversation_id: str) -> bool:
        """
        Clear feedback for a specific conversation (set to NULL)
        
        Args:
            conversation_id: The conversation ID to clear feedback for
            
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        
        if self.client and supabase_config.is_connected():
            return self._clear_feedback_in_database(conversation_id)
        else:
            return self._clear_feedback_in_json(conversation_id)
    
    def _clear_feedback_in_database(self, conversation_id: str) -> bool:
        """
        Clear feedback from conversations table in Supabase database
        """
        try:
            response = self.client.table(self.table_name).update({
                'feedback': None
            }).eq('id', conversation_id).execute()
            
            if response.data:
                logger.info(f"Feedback cleared for conversation: {conversation_id}")
                return True
            else:
                logger.error("Failed to clear feedback - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error clearing feedback from database: {e}")
            return self._clear_feedback_in_json(conversation_id)
    
    def _clear_feedback_in_json(self, conversation_id: str) -> bool:
        """
        Clear feedback from JSON file
        """
        try:
            if not self.fallback_file.exists():
                return False
            
            with open(self.fallback_file, 'r') as f:
                feedback_data = json.load(f)
            
            # Remove the feedback entry
            original_length = len(feedback_data)
            feedback_data = [
                entry for entry in feedback_data
                if entry.get('conversation_id') != conversation_id
            ]
            
            if len(feedback_data) < original_length:
                with open(self.fallback_file, 'w') as f:
                    json.dump(feedback_data, f, indent=2, default=str)
                logger.info(f"Feedback cleared from JSON for conversation: {conversation_id}")
                return True
            else:
                logger.warning(f"Feedback not found for conversation: {conversation_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error clearing feedback from JSON: {e}")
            return False

# Global instance
feedback_storage = FeedbackStorage()
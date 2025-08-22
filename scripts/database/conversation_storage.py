from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging
from .supabase_config import supabase_config

logger = logging.getLogger(__name__)

class ConversationStorage:
    """
    Handle conversation storage and retrieval using Supabase
    """
    
    def __init__(self):
        self.client = supabase_config.get_client()
        self.table_name = 'conversations'
    
    def store_conversation(self, 
                         session_id: str,
                         user_question: str, 
                         ta_response: str, 
                         context_sources: List[str] = None,
                         concepts_used: List[str] = None,
                         response_time: float = None) -> bool:
        """
        Store a conversation exchange in the database
        
        Args:
            session_id: Unique session identifier
            user_question: The student's question
            ta_response: The TA's response
            context_sources: List of source files used for context
            concepts_used: List of concepts identified in the conversation
            response_time: Time taken to generate response
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            logger.error("Supabase client not available")
            return False
        
        try:
            conversation_data = {
                'id': str(uuid.uuid4()),
                'session_id': session_id,
                'user_question': user_question,
                'ta_response': ta_response,
                'context_sources': context_sources or [],
                'concepts_used': concepts_used or [],
                'response_time': response_time,
                'created_at': datetime.now().isoformat(),
                'question_length': len(user_question),
                'response_length': len(ta_response)
            }
            
            response = self.client.table(self.table_name).insert(conversation_data).execute()
            
            if response.data:
                logger.info(f"Conversation stored successfully with ID: {conversation_data['id']}")
                return True
            else:
                logger.error("Failed to store conversation - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            return False
    
    def get_session_conversations(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all conversations for a specific session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation records
        """
        if not self.client:
            logger.error("Supabase client not available")
            return []
        
        try:
            response = self.client.table(self.table_name)\
                .select('*')\
                .eq('session_id', session_id)\
                .order('created_at', desc=False)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error retrieving session conversations: {e}")
            return []
    
    def get_recent_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent conversations for analytics
        
        Args:
            limit: Maximum number of conversations to retrieve
            
        Returns:
            List of recent conversation records
        """
        if not self.client:
            logger.error("Supabase client not available")
            return []
        
        try:
            response = self.client.table(self.table_name)\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error retrieving recent conversations: {e}")
            return []
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """
        Get basic statistics about stored conversations
        
        Returns:
            Dictionary with conversation statistics
        """
        if not self.client:
            logger.error("Supabase client not available")
            return {}
        
        try:
            # Get total count
            count_response = self.client.table(self.table_name)\
                .select('id', count='exact')\
                .execute()
            
            total_conversations = count_response.count or 0
            
            # Get recent conversations for additional stats
            recent = self.get_recent_conversations(limit=50)
            
            avg_response_time = 0
            avg_question_length = 0
            avg_response_length = 0
            
            if recent:
                response_times = [conv.get('response_time', 0) for conv in recent if conv.get('response_time')]
                question_lengths = [conv.get('question_length', 0) for conv in recent]
                response_lengths = [conv.get('response_length', 0) for conv in recent]
                
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                avg_question_length = sum(question_lengths) / len(question_lengths) if question_lengths else 0
                avg_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
            
            return {
                'total_conversations': total_conversations,
                'avg_response_time': round(avg_response_time, 2),
                'avg_question_length': round(avg_question_length, 1),
                'avg_response_length': round(avg_response_length, 1),
                'recent_sample_size': len(recent)
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {}
    
    def create_session_id(self) -> str:
        """
        Generate a new session ID
        
        Returns:
            New session ID string
        """
        return str(uuid.uuid4())

# Global instance
conversation_storage = ConversationStorage()
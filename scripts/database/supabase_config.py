import os
from supabase import create_client, Client
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SupabaseConfig:
    """
    Supabase database configuration and connection management
    """
    
    def __init__(self):
        self.url: Optional[str] = None
        self.key: Optional[str] = None
        self.client: Optional[Client] = None
        self._load_config()
    
    def _load_config(self):
        """
        Load Supabase configuration from environment variables
        """
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.url or not self.key:
            logger.warning("Supabase configuration not found. Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
            return
        
        try:
            self.client = create_client(self.url, self.key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    def get_client(self) -> Optional[Client]:
        """
        Get the Supabase client instance
        """
        return self.client
    
    def is_connected(self) -> bool:
        """
        Check if Supabase client is properly configured
        """
        return self.client is not None
    
    def test_connection(self) -> bool:
        """
        Test the database connection
        """
        if not self.client:
            return False
        
        try:
            # Try a simple query to test connection
            response = self.client.table('conversations').select('*').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

# Global instance
supabase_config = SupabaseConfig()
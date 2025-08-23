import os
from supabase import create_client, Client
from typing import Optional
import logging

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

logger = logging.getLogger(__name__)

class SupabaseConfig:
    """
    Supabase database configuration and connection management
    Reads configuration from Streamlit secrets or environment variables
    """
    
    def __init__(self):
        self.url: Optional[str] = None
        self.key: Optional[str] = None
        self.client: Optional[Client] = None
        self._load_config()
    
    def _load_config(self):
        """
        Load Supabase configuration from Streamlit secrets or environment variables
        Priority: Streamlit secrets > Environment variables
        """
        # Try to load from Streamlit secrets first
        if STREAMLIT_AVAILABLE and hasattr(st, 'secrets'):
            try:
                self.url = st.secrets.get('SUPABASE_URL')
                self.key = st.secrets.get('SUPABASE_ANON_KEY')
                if self.url and self.key:
                    logger.info("Loaded Supabase configuration from Streamlit secrets")
                else:
                    logger.info("Supabase configuration not found in Streamlit secrets")
            except Exception as e:
                logger.warning(f"Failed to load from Streamlit secrets: {e}")
        
        # Fallback to environment variables if not found in secrets
        if not self.url or not self.key:
            self.url = os.getenv('SUPABASE_URL')
            self.key = os.getenv('SUPABASE_ANON_KEY')
            if self.url and self.key:
                logger.info("Loaded Supabase configuration from environment variables")
        
        # Check if we have valid configuration
        if not self.url or not self.key:
            logger.warning(
                "Supabase configuration not found. Please configure SUPABASE_URL and SUPABASE_ANON_KEY in:\n"
                "1. Streamlit secrets (.streamlit/secrets.toml), or\n"
                "2. Environment variables\n"
                "Feedback will be stored in local JSON files as fallback."
            )
            return
        
        # Validate configuration format
        if not self.url.startswith('https://') or 'supabase.co' not in self.url:
            logger.warning("SUPABASE_URL format appears invalid. Expected format: https://your-project-ref.supabase.co")
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
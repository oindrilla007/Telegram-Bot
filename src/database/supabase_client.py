from supabase import create_client, Client
from config.config import Config
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            try:
                self._client = create_client(
                    Config.SUPABASE_URL,
                    Config.SUPABASE_KEY
                )
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                raise
    
    @property
    def client(self) -> Client:
        return self._client
    
    def test_connection(self):
        """Test the Supabase connection"""
        try:
            # Try to execute a simple query to test connection
            result = self._client.table('users').select("*").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False

# Create a global instance
supabase_client = SupabaseClient()
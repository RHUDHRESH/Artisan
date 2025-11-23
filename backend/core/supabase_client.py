"""
Supabase Client for cloud database and authentication
Optional - fallback to ChromaDB if not configured
"""
from typing import Optional, Dict, List, Any
from loguru import logger

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase not installed. Install with: pip install supabase")


class SupabaseClient:
    """
    Supabase client wrapper for database and auth operations
    """

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = url
        self.key = key
        self.client: Optional[Client] = None
        self.enabled = False

        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase SDK not available")
            return

        if url and key:
            try:
                self.client = create_client(url, key)
                self.enabled = True
                logger.info("✅ Supabase client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
                self.enabled = False
        else:
            logger.info("Supabase not configured - using local storage only")

    async def health_check(self) -> bool:
        """Check if Supabase is available"""
        if not self.enabled or not self.client:
            return False

        try:
            # Try a simple query to verify connection
            response = self.client.table('_health').select('*').limit(1).execute()
            return True
        except Exception as e:
            logger.debug(f"Supabase health check failed: {e}")
            return False

    async def save_user_profile(self, user_id: str, profile_data: Dict) -> bool:
        """Save user profile to Supabase"""
        if not self.enabled:
            logger.debug("Supabase not enabled, skipping profile save")
            return False

        try:
            self.client.table('user_profiles').upsert({
                'user_id': user_id,
                **profile_data
            }).execute()
            logger.info(f"Saved profile for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save user profile: {e}")
            return False

    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile from Supabase"""
        if not self.enabled:
            return None

        try:
            response = self.client.table('user_profiles').select('*').eq('user_id', user_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None

    async def save_search_results(self, user_id: str, search_type: str, results: List[Dict]) -> bool:
        """Save search results to Supabase"""
        if not self.enabled:
            return False

        try:
            self.client.table('search_results').insert({
                'user_id': user_id,
                'search_type': search_type,
                'results': results,
                'timestamp': 'now()'
            }).execute()
            logger.info(f"Saved {search_type} results for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save search results: {e}")
            return False

    async def get_recent_searches(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent searches from Supabase"""
        if not self.enabled:
            return []

        try:
            response = self.client.table('search_results') \
                .select('*') \
                .eq('user_id', user_id) \
                .order('timestamp', desc=True) \
                .limit(limit) \
                .execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to get recent searches: {e}")
            return []

    async def save_supplier(self, supplier_data: Dict) -> bool:
        """Save verified supplier to Supabase"""
        if not self.enabled:
            return False

        try:
            self.client.table('suppliers').upsert(supplier_data).execute()
            logger.info(f"Saved supplier: {supplier_data.get('name')}")
            return True
        except Exception as e:
            logger.error(f"Failed to save supplier: {e}")
            return False

    async def search_suppliers(
        self,
        query: str,
        location: Optional[str] = None,
        craft_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search suppliers in Supabase"""
        if not self.enabled:
            return []

        try:
            query_builder = self.client.table('suppliers').select('*')

            if location:
                query_builder = query_builder.ilike('location', f'%{location}%')

            if craft_type:
                query_builder = query_builder.ilike('products', f'%{craft_type}%')

            response = query_builder.limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to search suppliers: {e}")
            return []


# Global Supabase client instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client(url: Optional[str] = None, key: Optional[str] = None) -> SupabaseClient:
    """Get or create Supabase client instance"""
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = SupabaseClient(url=url, key=key)

    return _supabase_client

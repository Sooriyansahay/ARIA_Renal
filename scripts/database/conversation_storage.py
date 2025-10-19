from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
import logging
import os

# Official Supabase client
from supabase import create_client, Client

logger = logging.getLogger(__name__)

def _get_supabase_client() -> Optional[Client]:
    """Load Supabase URL/key from Streamlit secrets or env."""
    url = None
    key = None
    try:
        import streamlit as st
        url = st.secrets.get("SUPABASE_URL", None)
        key = st.secrets.get("SUPABASE_ANON_KEY", None)
    except Exception:
        pass
    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        logger.info("Supabase disabled; using local logging fallback in caller.")
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        logger.error(f"Supabase client init failed: {e}")
        return None


class ConversationStorage:
    """
    Handle conversation storage and retrieval using Supabase.
    Uses table 'ta_interactions' with columns:
      id uuid (PK), ts timestamptz default now(),
      session_id uuid, question text, response_length int,
      context_sources text[], concepts_used text[], response_time_ms int
    """

    def __init__(self):
        self.client: Optional[Client] = _get_supabase_client()
        self.table_name = "ta_interactions"

    def store_conversation(
        self,
        session_id: str,
        user_question: str,
        ta_response: str,
        context_sources: List[str] = None,
        concepts_used: List[str] = None,
        response_time: float = None,
    ) -> Optional[str]:
        """
        Store a conversation exchange. Returns conversation ID on success, None on failure.
        """
        if not self.client:
            logger.error("Supabase client not available")
            return None

        try:
            conversation_id = str(uuid.uuid4())
            payload = {
                "id": conversation_id,
                "session_id": session_id,
                "question": user_question,
                "response_length": len(ta_response or ""),
                "context_sources": context_sources or [],
                "concepts_used": concepts_used or [],
                "response_time_ms": int((response_time or 0) * 1000),
                # ts column auto-populates in DB; include here only if your schema lacks default:
                # "ts": datetime.now(timezone.utc).isoformat()
            }

            resp = self.client.table(self.table_name).insert(payload).execute()
            # supabase-py returns inserted row(s) unless RLS/Prefer alters it; treat no exception as success
            if getattr(resp, "data", None) is not None or True:
                logger.info(f"Conversation stored with ID: {conversation_id}")
                return conversation_id

        except Exception as e:
            logger.error(f"Error storing conversation: {e}")

        return None

    def get_session_conversations(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve all conversations for a specific session."""
        if not self.client:
            logger.error("Supabase client not available")
            return []
        try:
            resp = (
                self.client.table(self.table_name)
                .select("*")
                .eq("session_id", session_id)
                .order("ts", desc=False)
                .execute()
            )
            return resp.data or []
        except Exception as e:
            logger.error(f"Error retrieving session conversations: {e}")
            return []

    def get_recent_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent conversations for analytics."""
        if not self.client:
            logger.error("Supabase client not available")
            return []
        try:
            resp = (
                self.client.table(self.table_name)
                .select("*")
                .order("ts", desc=True)
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception as e:
            logger.error(f"Error retrieving recent conversations: {e}")
            return []

    def get_conversation_stats(self) -> Dict[str, Any]:
        """Basic statistics about stored conversations."""
        if not self.client:
            logger.error("Supabase client not available")
            return {}
        try:
            # total count
            count_resp = self.client.table(self.table_name).select("id", count="exact").execute()
            total = getattr(count_resp, "count", 0) or 0

            recent = self.get_recent_conversations(limit=50)
            rt = [c.get("response_time_ms", 0) for c in recent if c.get("response_time_ms") is not None]
            rl = [c.get("response_length", 0) for c in recent]

            avg_rt_ms = int(sum(rt) / len(rt)) if rt else 0
            avg_rl = round(sum(rl) / len(rl), 1) if rl else 0.0

            return {
                "total_conversations": total,
                "avg_response_time_ms": avg_rt_ms,
                "avg_response_length": avg_rl,
                "recent_sample_size": len(recent),
            }
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {}

    def create_session_id(self) -> str:
        return str(uuid.uuid4())


# Global instance
conversation_storage = ConversationStorage()

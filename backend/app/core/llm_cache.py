import json
import hashlib
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import BaseMessage, SystemMessage

from app.models.cache import LLMCache


class ContextAwareLLMCache:
    """Database-backed cache for LLM responses with conversation context awareness."""

    def __init__(self, context_window: int = 5):
        self.context_window = context_window

    def _get_cache_key(self, messages: List[BaseMessage], model: str) -> str:
        """Generate a cache key from messages INCLUDING conversation context."""
        # Filter out system messages
        non_system_messages = [m for m in messages if not isinstance(m, SystemMessage)]

        # Take last N messages for context (including current query)
        context_messages = non_system_messages[-self.context_window:]

        # Create a structured representation of the conversation context
        context_data = []
        for msg in context_messages:
            msg_data = {
                "role": msg.__class__.__name__,
                "content": str(msg.content)
            }
            # Include tool calls if present (for AIMessage)
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                msg_data["tool_calls"] = [
                    {"name": tc.get("name"), "args": tc.get("args")}
                    for tc in msg.tool_calls
                ]
            context_data.append(msg_data)

        # Create hash from the context
        content = json.dumps(context_data, sort_keys=True)
        context_hash = hashlib.sha256(content.encode()).hexdigest()

        return context_hash

    async def get(self, db: AsyncSession, messages: List[BaseMessage], model: str) -> Optional[dict]:
        """Retrieve cached response from database."""
        key = self._get_cache_key(messages, model)

        result = await db.execute(
            select(LLMCache).where(LLMCache.cache_key == key)
        )
        cached = result.scalar_one_or_none()

        if cached:
            return json.loads(cached.response)

        return None

    async def set(
        self,
        db: AsyncSession,
        messages: List[BaseMessage],
        model: str,
        response: dict
    ):
        """Store response in database cache."""
        key = self._get_cache_key(messages, model)

        # Check if key exists and update, otherwise insert
        result = await db.execute(
            select(LLMCache).where(LLMCache.cache_key == key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.response = json.dumps(response)
            existing.model = model
            existing.created_at = datetime.utcnow()
        else:
            cache_entry = LLMCache(
                cache_key=key,
                model=model,
                response=json.dumps(response)
            )
            db.add(cache_entry)

        await db.commit()

    async def delete(self, db: AsyncSession, messages: List[BaseMessage], model: str) -> bool:
        """Delete a specific cache entry. Returns True if entry was deleted."""
        key = self._get_cache_key(messages, model)

        result = await db.execute(
            delete(LLMCache).where(LLMCache.cache_key == key)
        )
        await db.commit()
        return result.rowcount > 0

    async def clear_all(self, db: AsyncSession) -> int:
        """Clear all cache entries. Returns count of deleted entries."""
        result = await db.execute(delete(LLMCache))
        await db.commit()
        return result.rowcount


# Singleton instance
llm_cache = ContextAwareLLMCache()

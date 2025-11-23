"""
Agent Memory System - Redis-backed memory for agents
Supports short-term, long-term, and shared memory
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger
import json
import redis
from redis import asyncio as aioredis


class MemoryEntry(BaseModel):
    """Single memory entry"""
    key: str
    value: Any
    timestamp: datetime
    agent_id: str
    memory_type: str  # short_term, long_term, shared
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class AgentMemoryManager:
    """
    Manages agent memory using Redis
    Supports different memory types and TTLs
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600  # 1 hour
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client: Optional[aioredis.Redis] = None
        logger.info(f"🧠 Agent Memory Manager initializing...")

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis for agent memory")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory fallback")
            self.redis_client = None

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()

    def _make_key(self, agent_id: str, memory_type: str, key: str) -> str:
        """Generate Redis key"""
        return f"agent:{agent_id}:{memory_type}:{key}"

    async def store(
        self,
        agent_id: str,
        key: str,
        value: Any,
        memory_type: str = "short_term",
        ttl: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):
        """Store data in agent memory"""
        if not self.redis_client:
            logger.warning("Redis not available, memory not stored")
            return

        redis_key = self._make_key(agent_id, memory_type, key)
        ttl = ttl or (self.default_ttl if memory_type == "short_term" else None)

        entry = MemoryEntry(
            key=key,
            value=value,
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            memory_type=memory_type,
            expires_at=datetime.utcnow() + timedelta(seconds=ttl) if ttl else None,
            metadata=metadata or {}
        )

        await self.redis_client.set(
            redis_key,
            entry.model_dump_json(),
            ex=ttl
        )

        logger.debug(f"💾 Stored {memory_type} memory for {agent_id}: {key}")

    async def retrieve(
        self,
        agent_id: str,
        key: str,
        memory_type: str = "short_term"
    ) -> Optional[Any]:
        """Retrieve data from agent memory"""
        if not self.redis_client:
            return None

        redis_key = self._make_key(agent_id, memory_type, key)
        data = await self.redis_client.get(redis_key)

        if data:
            entry = MemoryEntry.model_validate_json(data)
            logger.debug(f"🔍 Retrieved {memory_type} memory for {agent_id}: {key}")
            return entry.value

        return None

    async def delete(
        self,
        agent_id: str,
        key: str,
        memory_type: str = "short_term"
    ):
        """Delete memory entry"""
        if not self.redis_client:
            return

        redis_key = self._make_key(agent_id, memory_type, key)
        await self.redis_client.delete(redis_key)
        logger.debug(f"🗑️ Deleted {memory_type} memory for {agent_id}: {key}")

    async def get_all_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None
    ) -> List[MemoryEntry]:
        """Get all memories for an agent"""
        if not self.redis_client:
            return []

        pattern = f"agent:{agent_id}:{memory_type or '*'}:*"
        keys = await self.redis_client.keys(pattern)

        memories = []
        for key in keys:
            data = await self.redis_client.get(key)
            if data:
                memories.append(MemoryEntry.model_validate_json(data))

        return memories

    async def clear_agent_memory(
        self,
        agent_id: str,
        memory_type: Optional[str] = None
    ):
        """Clear all memories for an agent"""
        if not self.redis_client:
            return

        pattern = f"agent:{agent_id}:{memory_type or '*'}:*"
        keys = await self.redis_client.keys(pattern)

        if keys:
            await self.redis_client.delete(*keys)
            logger.info(f"🧹 Cleared {len(keys)} memories for agent {agent_id}")

    # Specialized memory operations

    async def store_conversation(
        self,
        agent_id: str,
        conversation_id: str,
        messages: List[Dict],
        ttl: int = 3600
    ):
        """Store conversation history"""
        await self.store(
            agent_id=agent_id,
            key=f"conversation:{conversation_id}",
            value=messages,
            memory_type="short_term",
            ttl=ttl,
            metadata={"type": "conversation", "message_count": len(messages)}
        )

    async def get_conversation(
        self,
        agent_id: str,
        conversation_id: str
    ) -> List[Dict]:
        """Retrieve conversation history"""
        result = await self.retrieve(
            agent_id=agent_id,
            key=f"conversation:{conversation_id}",
            memory_type="short_term"
        )
        return result or []

    async def store_task_result(
        self,
        agent_id: str,
        task_id: str,
        result: Any,
        ttl: int = 86400  # 24 hours
    ):
        """Store task execution result"""
        await self.store(
            agent_id=agent_id,
            key=f"task_result:{task_id}",
            value=result,
            memory_type="long_term",
            ttl=ttl,
            metadata={"type": "task_result", "task_id": task_id}
        )

    async def get_task_result(
        self,
        agent_id: str,
        task_id: str
    ) -> Optional[Any]:
        """Retrieve task result"""
        return await self.retrieve(
            agent_id=agent_id,
            key=f"task_result:{task_id}",
            memory_type="long_term"
        )

    async def store_shared_knowledge(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Store knowledge shared across all agents"""
        await self.store(
            agent_id="global",
            key=key,
            value=value,
            memory_type="shared",
            ttl=ttl,
            metadata={"type": "shared_knowledge"}
        )

    async def get_shared_knowledge(
        self,
        key: str
    ) -> Optional[Any]:
        """Retrieve shared knowledge"""
        return await self.retrieve(
            agent_id="global",
            key=key,
            memory_type="shared"
        )

    # Analytics

    async def get_memory_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get memory statistics for an agent"""
        if not self.redis_client:
            return {"error": "Redis not available"}

        stats = {
            "agent_id": agent_id,
            "memory_types": {}
        }

        for memory_type in ["short_term", "long_term", "shared"]:
            pattern = f"agent:{agent_id}:{memory_type}:*"
            keys = await self.redis_client.keys(pattern)
            stats["memory_types"][memory_type] = len(keys)

        stats["total_entries"] = sum(stats["memory_types"].values())

        return stats


class ConversationBuffer:
    """
    Manages conversation history with sliding window
    """

    def __init__(
        self,
        memory_manager: AgentMemoryManager,
        agent_id: str,
        max_messages: int = 20
    ):
        self.memory_manager = memory_manager
        self.agent_id = agent_id
        self.max_messages = max_messages
        self.buffer: List[Dict] = []

    async def add_message(self, role: str, content: str):
        """Add message to buffer"""
        self.buffer.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep only last N messages
        if len(self.buffer) > self.max_messages:
            self.buffer = self.buffer[-self.max_messages:]

        # Store in Redis
        await self.memory_manager.store(
            agent_id=self.agent_id,
            key="conversation_buffer",
            value=self.buffer,
            memory_type="short_term",
            ttl=3600
        )

    async def get_messages(self) -> List[Dict]:
        """Get all messages in buffer"""
        # Try to load from Redis first
        stored = await self.memory_manager.retrieve(
            agent_id=self.agent_id,
            key="conversation_buffer",
            memory_type="short_term"
        )

        if stored:
            self.buffer = stored

        return self.buffer

    async def clear(self):
        """Clear conversation buffer"""
        self.buffer = []
        await self.memory_manager.delete(
            agent_id=self.agent_id,
            key="conversation_buffer",
            memory_type="short_term"
        )


# Global memory manager
_memory_manager: Optional[AgentMemoryManager] = None


async def get_memory_manager(redis_url: str = "redis://localhost:6379") -> AgentMemoryManager:
    """Get or create memory manager"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = AgentMemoryManager(redis_url)
        await _memory_manager.connect()
    return _memory_manager

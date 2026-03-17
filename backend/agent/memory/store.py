"""Persistent memory store backed by PostgreSQL."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agent.memory.models import MemoryEntry


class PersistentMemoryStore:
    """Async database-backed memory store.

    Supports per-conversation and global memory namespaces.
    All write operations create new state rather than mutating existing objects.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        conversation_id: uuid.UUID | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._conversation_id = conversation_id

    async def store(self, key: str, value: str, namespace: str = "default") -> None:
        """Store or update a key-value pair."""
        if not key.strip():
            raise ValueError("Key must not be empty")
        if not value:
            raise ValueError("Value must not be empty")

        async with self._session_factory() as session:
            stmt = select(MemoryEntry).where(
                MemoryEntry.namespace == namespace,
                MemoryEntry.key == key,
                MemoryEntry.conversation_id == self._conversation_id,
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing is not None:
                await session.execute(
                    update(MemoryEntry)
                    .where(
                        MemoryEntry.conversation_id == self._conversation_id,
                        MemoryEntry.namespace == namespace,
                        MemoryEntry.key == key,
                    )
                    .values(value=value)
                )
            else:
                entry = MemoryEntry(
                    namespace=namespace,
                    key=key,
                    value=value,
                    conversation_id=self._conversation_id,
                )
                session.add(entry)

            await session.commit()

    async def recall(
        self, query: str, namespace: str = "default", limit: int = 20
    ) -> list[dict[str, str]]:
        """Search memory entries by substring match on key and value.

        Searches both conversation-specific and global memories.
        """
        if not query.strip():
            return []

        query_lower = f"%{query.lower()}%"
        async with self._session_factory() as session:
            stmt = (
                select(MemoryEntry)
                .where(
                    MemoryEntry.namespace == namespace,
                    or_(
                        MemoryEntry.conversation_id == self._conversation_id,
                        MemoryEntry.conversation_id.is_(None),
                    ),
                    or_(
                        func.lower(MemoryEntry.key).like(query_lower),
                        func.lower(MemoryEntry.value).like(query_lower),
                    ),
                )
                .order_by(MemoryEntry.updated_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            entries = result.scalars().all()

            return [
                {
                    "namespace": e.namespace,
                    "key": e.key,
                    "value": e.value,
                    "scope": "conversation" if e.conversation_id else "global",
                }
                for e in entries
            ]

    async def list_entries(
        self, namespace: str = "default", limit: int = 50
    ) -> list[dict[str, str]]:
        """List all memory entries in a namespace."""
        async with self._session_factory() as session:
            stmt = (
                select(MemoryEntry)
                .where(
                    MemoryEntry.namespace == namespace,
                    or_(
                        MemoryEntry.conversation_id == self._conversation_id,
                        MemoryEntry.conversation_id.is_(None),
                    ),
                )
                .order_by(MemoryEntry.updated_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            entries = result.scalars().all()

            return [
                {
                    "namespace": e.namespace,
                    "key": e.key,
                    "value": e.value,
                    "scope": "conversation" if e.conversation_id else "global",
                }
                for e in entries
            ]

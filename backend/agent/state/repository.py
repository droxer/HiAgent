"""PostgreSQL repository for conversation persistence.

All methods receive an ``AsyncSession`` via dependency injection.
All returned records are frozen dataclasses from ``schemas.py`` —
ORM models never leak beyond this module.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.state.models import (
    AgentRunModel,
    ArtifactModel,
    ConversationModel,
    EventModel,
    MessageModel,
)
from agent.state.schemas import (
    AgentRunRecord,
    ArtifactRecord,
    ConversationRecord,
    EventRecord,
    MessageRecord,
)


def _to_conversation(model: ConversationModel) -> ConversationRecord:
    return ConversationRecord(
        id=model.id,
        title=model.title,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_message(model: MessageModel) -> MessageRecord:
    return MessageRecord(
        id=model.id,
        conversation_id=model.conversation_id,
        role=model.role,
        content=model.content,
        iteration=model.iteration,
        created_at=model.created_at,
    )


def _to_event(model: EventModel) -> EventRecord:
    return EventRecord(
        id=model.id,
        conversation_id=model.conversation_id,
        event_type=model.event_type,
        data=model.data,
        iteration=model.iteration,
        timestamp=model.timestamp,
    )


def _to_agent_run(model: AgentRunModel) -> AgentRunRecord:
    return AgentRunRecord(
        id=model.id,
        conversation_id=model.conversation_id,
        config=model.config,
        status=model.status,
        result=model.result,
        created_at=model.created_at,
    )


def _to_artifact(model: ArtifactModel) -> ArtifactRecord:
    return ArtifactRecord(
        id=model.id,
        conversation_id=model.conversation_id,
        storage_key=model.storage_key,
        original_name=model.original_name,
        content_type=model.content_type,
        size=model.size,
        created_at=model.created_at,
    )


class ConversationRepository:
    """Async repository for conversation persistence backed by PostgreSQL."""

    async def create_conversation(
        self,
        session: AsyncSession,
        title: str | None = None,
        conversation_id: uuid.UUID | None = None,
    ) -> ConversationRecord:
        model = ConversationModel(id=conversation_id or uuid.uuid4(), title=title)
        session.add(model)
        await session.flush()
        await session.refresh(model)  # need generated id/timestamps before returning
        await session.commit()
        return _to_conversation(model)

    async def get_conversation(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
    ) -> ConversationRecord | None:
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation_id
        )
        result = await session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_conversation(model) if model else None

    async def list_conversations(
        self,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> tuple[list[ConversationRecord], int]:
        count_stmt = select(func.count()).select_from(ConversationModel)
        if search:
            count_stmt = count_stmt.where(
                ConversationModel.title.ilike(f"%{search}%")
            )
        total = (await session.execute(count_stmt)).scalar_one()

        stmt = (
            select(ConversationModel)
            .order_by(ConversationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if search:
            stmt = stmt.where(ConversationModel.title.ilike(f"%{search}%"))
        result = await session.execute(stmt)
        items = [_to_conversation(m) for m in result.scalars().all()]
        return items, total

    async def delete_conversation(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
    ) -> bool:
        """Delete a conversation by ID. Returns True if found and deleted."""
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation_id
        )
        result = await session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await session.delete(model)
        await session.commit()
        return True

    async def update_conversation(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
        title: str | None = None,
    ) -> ConversationRecord:
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation_id
        )
        result = await session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Conversation not found: {conversation_id}")

        if title is not None:
            model.title = title
        model.updated_at = datetime.now(timezone.utc)

        await session.commit()
        await session.refresh(model)  # refresh after commit to get final state
        return _to_conversation(model)

    async def save_message(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
        role: str,
        content: dict,
        iteration: int | None = None,
    ) -> MessageRecord:
        model = MessageModel(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            iteration=iteration,
        )
        session.add(model)
        await session.flush()
        await session.refresh(model)  # need generated timestamps before returning
        await session.commit()
        return _to_message(model)

    async def get_messages(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
    ) -> list[MessageRecord]:
        stmt = (
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at.asc())
        )
        result = await session.execute(stmt)
        return [_to_message(m) for m in result.scalars().all()]

    async def save_event(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
        event_type: str,
        data: dict,
        iteration: int | None = None,
    ) -> None:
        model = EventModel(
            conversation_id=conversation_id,
            event_type=event_type,
            data=data,
            iteration=iteration,
        )
        session.add(model)
        await session.commit()

    async def get_events(
        self,
        session: AsyncSession,
        conversation_id: uuid.UUID,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[EventRecord]:
        stmt = (
            select(EventModel)
            .where(EventModel.conversation_id == conversation_id)
            .order_by(EventModel.timestamp.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        return [_to_event(m) for m in result.scalars().all()]

    async def save_artifact(
        self,
        session: AsyncSession,
        artifact_id: str,
        conversation_id: uuid.UUID,
        storage_key: str,
        original_name: str,
        content_type: str,
        size: int,
    ) -> ArtifactRecord:
        model = ArtifactModel(
            id=artifact_id,
            conversation_id=conversation_id,
            storage_key=storage_key,
            original_name=original_name,
            content_type=content_type,
            size=size,
        )
        session.add(model)
        await session.flush()
        await session.refresh(model)  # need generated timestamps before returning
        await session.commit()
        return _to_artifact(model)

    async def get_artifact(
        self,
        session: AsyncSession,
        artifact_id: str,
    ) -> ArtifactRecord | None:
        stmt = select(ArtifactModel).where(ArtifactModel.id == artifact_id)
        result = await session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_artifact(model) if model else None

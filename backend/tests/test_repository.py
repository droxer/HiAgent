"""Integration tests for ConversationRepository.

Requires a running PostgreSQL instance.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agent.state.models import Base
from agent.state.repository import ConversationRepository

TEST_DB_URL = "postgresql+asyncpg://ha:ha@localhost:5432/hiagent"


@pytest_asyncio.fixture
async def session():
    """Create a session with clean data. Uses TRUNCATE, never drops tables."""
    engine = create_async_engine(TEST_DB_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    # Truncate all tables before each test (preserves schema)
    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text(
                "TRUNCATE conversations, messages, events, agent_runs CASCADE"
            )
        )
    async with factory() as sess:
        yield sess
    await engine.dispose()


@pytest.fixture
def repo() -> ConversationRepository:
    return ConversationRepository()


class TestCreateConversation:
    async def test_creates_with_title(self, repo, session: AsyncSession) -> None:
        record = await repo.create_conversation(session, title="Test convo")
        assert record.title == "Test convo"
        assert record.id is not None

    async def test_creates_without_title(self, repo, session: AsyncSession) -> None:
        record = await repo.create_conversation(session, title=None)
        assert record.title is None


class TestGetConversation:
    async def test_returns_none_for_missing(self, repo, session: AsyncSession) -> None:
        result = await repo.get_conversation(session, uuid.uuid4())
        assert result is None

    async def test_returns_existing(self, repo, session: AsyncSession) -> None:
        created = await repo.create_conversation(session, title="Find me")
        found = await repo.get_conversation(session, created.id)
        assert found is not None
        assert found.id == created.id
        assert found.title == "Find me"


class TestListConversations:
    async def test_paginated_list(self, repo, session: AsyncSession) -> None:
        for i in range(5):
            await repo.create_conversation(session, title=f"Convo {i}")
        items, total = await repo.list_conversations(session, limit=2, offset=0)
        assert len(items) == 2
        assert total == 5

    async def test_offset(self, repo, session: AsyncSession) -> None:
        for i in range(3):
            await repo.create_conversation(session, title=f"Convo {i}")
        items, total = await repo.list_conversations(session, limit=10, offset=2)
        assert len(items) == 1
        assert total == 3


class TestUpdateConversation:
    async def test_update_title(self, repo, session: AsyncSession) -> None:
        created = await repo.create_conversation(session, title="Old")
        updated = await repo.update_conversation(session, created.id, title="New")
        assert updated.title == "New"


class TestMessages:
    async def test_save_and_get_messages(self, repo, session: AsyncSession) -> None:
        convo = await repo.create_conversation(session, title="Messages test")
        await repo.save_message(
            session, convo.id, role="user", content={"text": "hello"}, iteration=None
        )
        await repo.save_message(
            session,
            convo.id,
            role="assistant",
            content={"text": "hi there"},
            iteration=1,
        )
        messages = await repo.get_messages(session, convo.id)
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert messages[1].iteration == 1


class TestEvents:
    async def test_save_and_get_events(self, repo, session: AsyncSession) -> None:
        convo = await repo.create_conversation(session, title="Events test")
        await repo.save_event(
            session,
            convo.id,
            event_type="task_start",
            data={"message": "hello"},
            iteration=1,
        )
        events = await repo.get_events(session, convo.id, limit=10, offset=0)
        assert len(events) == 1
        assert events[0].event_type == "task_start"

    async def test_save_event_flushes_before_commit(self, repo, session: AsyncSession) -> None:
        """Verify save_event persists correctly with flush+commit pattern."""
        convo = await repo.create_conversation(session, title="Flush test")
        await repo.save_event(
            session,
            convo.id,
            event_type="tool_result",
            data={"output": "42"},
            iteration=2,
        )
        # Re-read from DB to confirm persistence
        events = await repo.get_events(session, convo.id)
        assert len(events) == 1
        assert events[0].data == {"output": "42"}
        assert events[0].iteration == 2


class TestArtifacts:
    async def test_save_artifact_flushes_before_commit(self, repo, session: AsyncSession) -> None:
        """Verify save_artifact persists correctly with flush+refresh+commit."""
        convo = await repo.create_conversation(session, title="Artifact flush test")
        artifact = await repo.save_artifact(
            session,
            artifact_id="abc123",
            conversation_id=convo.id,
            storage_key="store/abc123",
            original_name="image.png",
            content_type="image/png",
            size=1024,
        )
        assert artifact.id == "abc123"
        assert artifact.original_name == "image.png"
        assert artifact.size == 1024

        # Re-read from DB
        fetched = await repo.get_artifact(session, "abc123")
        assert fetched is not None
        assert fetched.storage_key == "store/abc123"

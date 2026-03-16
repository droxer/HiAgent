"""Database event subscriber for persisting agent events to PostgreSQL.

Registered on the EventEmitter for each conversation. Persists events,
messages, and status updates without coupling the orchestrator to the
database. Transient failures are retried with exponential backoff;
permanent failures are logged at error level and never propagate.
"""

from __future__ import annotations

import asyncio
import dataclasses
import uuid
from typing import Any

from loguru import logger
from sqlalchemy.exc import IntegrityError, OperationalError, InterfaceError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agent.state.repository import ConversationRepository
from api.events import AgentEvent, EventType

# Event types that should not be persisted (too noisy or ephemeral)
_SKIP_EVENTS = {EventType.TEXT_DELTA}

# Retry configuration
_MAX_RETRIES = 3
_BASE_DELAY = 0.1  # seconds — delays: 0.1, 0.3, 0.9

# Exceptions worth retrying (transient / connection issues)
_RETRYABLE_EXCEPTIONS = (OperationalError, InterfaceError, TimeoutError, OSError)


class PendingWrites:
    """Tracks in-flight DB writes so shutdown can wait for them to drain."""

    def __init__(self) -> None:
        self._count = 0
        self._drained = asyncio.Event()
        self._drained.set()  # starts drained (no pending writes)

    @property
    def count(self) -> int:
        return self._count

    def _increment(self) -> None:
        self._count += 1
        self._drained.clear()

    def _decrement(self) -> None:
        self._count = max(0, self._count - 1)
        if self._count == 0:
            self._drained.set()

    class _Tracker:
        def __init__(self, pending: PendingWrites) -> None:
            self._pending = pending

        async def __aenter__(self) -> None:
            self._pending._increment()

        async def __aexit__(self, *_: Any) -> None:
            self._pending._decrement()

    def track(self) -> _Tracker:
        return self._Tracker(self)

    async def wait_drained(self, timeout: float = 5.0) -> bool:
        """Wait until all pending writes complete. Returns False on timeout."""
        try:
            await asyncio.wait_for(self._drained.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.warning(
                "pending_writes_drain_timeout remaining={} timeout={:.1f}",
                self._count,
                timeout,
            )
            return False


def _make_serializable(value: Any) -> Any:
    """Recursively convert non-JSON-serializable objects to plain types."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, dict):
        return {k: _make_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_make_serializable(item) for item in value]
    return value


def _clean_data(data: dict[str, Any]) -> dict[str, Any]:
    """Remove non-serializable entries (e.g. callbacks) and convert
    dataclass values to plain dicts for JSONB storage."""
    cleaned = {
        k: v for k, v in data.items()
        if not callable(v) and k != "response_callback"
    }
    return _make_serializable(cleaned)


async def _retry_with_backoff(
    func: Any,
    conversation_id: uuid.UUID,
    event: AgentEvent,
    clean_data: dict[str, Any],
) -> None:
    """Execute ``func`` with exponential backoff on transient errors."""
    last_exc: BaseException | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            await func()
            return
        except _RETRYABLE_EXCEPTIONS as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES - 1:
                delay = _BASE_DELAY * (3 ** attempt)
                logger.warning(
                    "db_subscriber_retry attempt={}/{} delay={:.2f}s "
                    "conversation_id={} event_type={} error={}",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                    conversation_id,
                    event.type.value,
                    exc,
                )
                await asyncio.sleep(delay)
        except (IntegrityError, ProgrammingError) as exc:
            # Non-retryable: constraint violation or SQL error
            logger.error(
                "db_subscriber_event_lost_non_retryable "
                "conversation_id={} event_type={} error={} data={}",
                conversation_id,
                event.type.value,
                exc,
                clean_data,
            )
            return

    # All retries exhausted
    logger.error(
        "db_subscriber_event_lost "
        "conversation_id={} event_type={} error={} data={}",
        conversation_id,
        event.type.value,
        last_exc,
        clean_data,
    )


def create_db_subscriber(
    conversation_id: uuid.UUID,
    repo: ConversationRepository,
    session_factory: async_sessionmaker[AsyncSession],
    pending_writes: PendingWrites | None = None,
) -> Any:
    """Create an async event subscriber that persists to PostgreSQL."""

    async def _subscriber(event: AgentEvent) -> None:
        if event.type in _SKIP_EVENTS:
            return

        clean = _clean_data(event.data)

        async def _do_write() -> None:
            async with session_factory() as session:
                if event.type == EventType.TURN_START:
                    message = clean.get("message", "")
                    await repo.save_message(
                        session,
                        conversation_id,
                        role="user",
                        content={"text": message},
                        iteration=None,
                    )

                elif event.type == EventType.TURN_COMPLETE:
                    result = clean.get("result", "")
                    await repo.save_message(
                        session,
                        conversation_id,
                        role="assistant",
                        content={"text": result},
                        iteration=event.iteration,
                    )

                elif event.type == EventType.TASK_COMPLETE:
                    result = clean.get("summary", clean.get("result", ""))
                    await repo.save_message(
                        session,
                        conversation_id,
                        role="assistant",
                        content={"text": result},
                        iteration=event.iteration,
                    )

                elif event.type == EventType.TASK_ERROR:
                    await repo.save_event(
                        session,
                        conversation_id,
                        event_type=event.type.value,
                        data=clean,
                        iteration=event.iteration,
                    )

                elif event.type == EventType.ARTIFACT_CREATED:
                    await repo.save_artifact(
                        session,
                        artifact_id=str(clean.get("artifact_id", "")),
                        conversation_id=conversation_id,
                        storage_key=str(clean.get("storage_key", clean.get("artifact_id", ""))),
                        original_name=str(clean.get("name", "")),
                        content_type=str(clean.get("content_type", "application/octet-stream")),
                        size=int(clean.get("size", 0)),
                    )

                elif event.type == EventType.CONVERSATION_TITLE:
                    title = clean.get("title", "")
                    if title:
                        await repo.update_conversation(
                            session, conversation_id, title=title
                        )

                else:
                    await repo.save_event(
                        session,
                        conversation_id,
                        event_type=event.type.value,
                        data=clean,
                        iteration=event.iteration,
                    )

        try:
            if pending_writes is not None:
                async with pending_writes.track():
                    await _retry_with_backoff(
                        _do_write, conversation_id, event, clean
                    )
            else:
                await _retry_with_backoff(
                    _do_write, conversation_id, event, clean
                )
        except Exception:
            logger.error(
                "db_subscriber_event_lost_unexpected "
                "conversation_id={} event_type={} data={}",
                conversation_id,
                event.type.value,
                clean,
                exc_info=True,
            )

    return _subscriber

"""FastAPI application with SSE streaming for conversation-based agent."""

from __future__ import annotations

import asyncio
import json
import os
import time as _time
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any, Protocol

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from agent.artifacts.manager import ArtifactManager
from agent.artifacts.storage import (
    LocalStorageBackend,
    StorageBackend,
    create_storage_backend,
)
from agent.llm.client import ClaudeClient
from agent.loop.orchestrator import AgentOrchestrator
from agent.loop.planner import PlannerOrchestrator
from agent.loop.sub_agent_manager import SubAgentManager
from agent.sandbox.base import SandboxProvider
from agent.tools.executor import ToolExecutor
from agent.tools.local.ask_user import AskUser
from agent.tools.local.memory_recall import MemoryRecall
from agent.tools.local.memory_store import MemoryStore
from agent.tools.local.message_user import MessageUser
from agent.tools.local.task_complete import TaskComplete
from agent.tools.local.image_gen import ImageGen
from agent.tools.local.web_fetch import WebFetch
from agent.tools.local.web_search import TavilyWebSearch
from agent.tools.registry import ToolRegistry
from agent.tools.sandbox.code_interpret import CodeInterpret
from agent.tools.sandbox.code_run import CodeRun
from agent.tools.sandbox.file_ops import FileEdit, FileList, FileRead, FileWrite
from agent.tools.sandbox.package_install import PackageInstall
from agent.tools.sandbox.shell_exec import ShellExec
from api.events import AgentEvent, EventEmitter, EventType
from config.settings import get_settings
from agent.state.database import get_engine, get_session, get_session_factory, init_db
from agent.state.repository import ConversationRepository
from api.db_subscriber import PendingWrites, create_db_subscriber

# UUID pattern for path parameter validation
_UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

# Max event queue size for backpressure
_EVENT_QUEUE_MAXSIZE = 5000

# Stale conversation TTL in seconds (1 hour)
_CONVERSATION_TTL_SECONDS = 3600


# ---------------------------------------------------------------------------
# Authentication & rate limiting
# ---------------------------------------------------------------------------

_security = HTTPBearer(auto_error=False)


async def _verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> None:
    """Verify API key if one is configured. No-op when API_KEY is empty."""
    settings = get_settings()
    if not settings.API_KEY:
        return
    if credentials is None or credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class _RateLimiter:
    """Simple in-memory sliding-window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> bool:
        now = _time.monotonic()
        window_start = now - self._window
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        if len(self._requests[key]) >= self._max:
            return False
        self._requests[key].append(now)
        return True


_rate_limiter: _RateLimiter | None = None


async def _check_rate_limit(request: Request) -> None:
    """Enforce per-IP rate limiting (disabled in development)."""
    settings = get_settings()
    if settings.ENVIRONMENT == "development":
        return
    global _rate_limiter  # noqa: PLW0603
    if _rate_limiter is None:
        _rate_limiter = _RateLimiter(max_requests=settings.RATE_LIMIT_PER_MINUTE)
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


# ---------------------------------------------------------------------------
# Callback holder — avoids two-phase orchestrator construction (H3 fix)
# ---------------------------------------------------------------------------


class _CallbackHolder:
    """Mutable holder for a completion callback."""

    def __init__(self) -> None:
        self._callback: Callable[..., Any] | None = None

    async def __call__(self, summary: str) -> None:
        if self._callback is not None:
            await self._callback(summary)

    def set(self, callback: Callable[..., Any]) -> None:
        self._callback = callback


# ---------------------------------------------------------------------------
# Protocols & models
# ---------------------------------------------------------------------------


class Runnable(Protocol):
    """Protocol for orchestrators that can run a turn."""

    async def run(self, user_message: str) -> str: ...


class ConversationEntry:
    """Container for a conversation's resources. Lives across multiple turns."""

    __slots__ = (
        "emitter",
        "event_queue",
        "pending_callbacks",
        "subscriber",
        "orchestrator",
        "executor",
        "turn_task",
        "created_at",
    )

    def __init__(
        self,
        emitter: EventEmitter,
        event_queue: asyncio.Queue[AgentEvent | None],
        orchestrator: Runnable,
        executor: ToolExecutor,
        pending_callbacks: dict[str, Any],
    ) -> None:
        self.emitter = emitter
        self.event_queue = event_queue
        self.orchestrator = orchestrator
        self.executor = executor
        self.pending_callbacks = pending_callbacks
        self.subscriber: Any = None
        self.turn_task: asyncio.Task[str] | None = None
        self.created_at: float = _time.monotonic()


# In-memory conversation store
_conversations: dict[str, ConversationEntry] = {}


class MessageRequest(BaseModel):
    """Request body for creating a conversation or sending a message."""

    message: str = Field(max_length=100_000)
    use_planner: bool = Field(
        default=False,
        description="When True, use PlannerOrchestrator to decompose into sub-tasks.",
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be empty")
        return v


class ConversationResponse(BaseModel):
    """Response body for conversation endpoints."""

    conversation_id: str


class UserInputRequest(BaseModel):
    """Request body for POST /conversations/{id}/respond."""

    request_id: str
    response: str = Field(max_length=50000)


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------


def _build_claude_client() -> ClaudeClient:
    """Build a ClaudeClient from settings."""
    settings = get_settings()
    return ClaudeClient(
        api_key=settings.ANTHROPIC_API_KEY,
        default_model=settings.TASK_MODEL,
        base_url=settings.ANTHROPIC_BASE_URL,
    )


def _build_sandbox_provider() -> tuple[SandboxProvider, Any]:
    """Create a sandbox provider based on SANDBOX_PROVIDER setting.

    Returns the provider and an optional pool (for shutdown draining).
    """
    settings = get_settings()
    provider = settings.SANDBOX_PROVIDER

    if provider == "boxlite":
        from agent.sandbox.boxlite_provider import BoxliteProvider

        logger.info("Using BoxliteProvider (micro-VM sandbox)")
        return BoxliteProvider(), None

    if provider == "e2b":
        from agent.sandbox.e2b_pool import SandboxPool
        from agent.sandbox.e2b_provider import E2BProvider

        api_key = settings.E2B_API_KEY
        if not api_key:
            raise RuntimeError("SANDBOX_PROVIDER=e2b but E2B_API_KEY is not set")
        pool = SandboxPool(api_key=api_key)
        logger.info("Using E2BProvider (cloud sandbox) with pooling")
        return E2BProvider(api_key=api_key, pool=pool), pool

    raise ValueError(
        f"Unknown SANDBOX_PROVIDER={provider!r}. Must be 'boxlite' or 'e2b'."
    )


def _build_base_registry(
    event_emitter: EventEmitter,
    on_complete: Any,
    artifact_manager: ArtifactManager | None = None,
) -> ToolRegistry:
    """Build the shared tool registry with all standard tools registered."""
    settings = get_settings()
    memory: dict[str, str] = {}

    registry = ToolRegistry()
    # Local tools
    registry = registry.register(TavilyWebSearch(api_key=settings.TAVILY_API_KEY))
    registry = registry.register(WebFetch())
    registry = registry.register(MessageUser(event_emitter=event_emitter))
    registry = registry.register(AskUser(event_emitter=event_emitter))
    registry = registry.register(TaskComplete(on_complete=on_complete))
    registry = registry.register(MemoryStore(store=memory))
    registry = registry.register(MemoryRecall(store=memory))

    # Conditionally register image_gen when API key is configured
    if settings.MINIMAX_API_KEY and artifact_manager is not None:
        registry = registry.register(
            ImageGen(
                api_key=settings.MINIMAX_API_KEY,
                artifact_manager=artifact_manager,
                event_emitter=event_emitter,
                api_host=settings.MINIMAX_API_HOST,
            )
        )

    # Sandbox tools
    registry = registry.register(CodeRun())
    registry = registry.register(ShellExec())
    registry = registry.register(CodeInterpret())
    registry = registry.register(FileRead())
    registry = registry.register(FileWrite())
    registry = registry.register(FileEdit())
    registry = registry.register(FileList())
    registry = registry.register(PackageInstall())
    return registry


def _build_sub_agent_registry_factory(
    event_emitter: EventEmitter,
    sandbox_provider: SandboxProvider,
) -> Callable[[], ToolRegistry]:
    """Factory that produces fully-populated registries for sub-agents (C1 fix)."""

    def factory() -> ToolRegistry:
        settings = get_settings()
        memory: dict[str, str] = {}
        registry = ToolRegistry()
        registry = registry.register(TavilyWebSearch(api_key=settings.TAVILY_API_KEY))
        registry = registry.register(WebFetch())
        registry = registry.register(MessageUser(event_emitter=event_emitter))
        registry = registry.register(MemoryStore(store=memory))
        registry = registry.register(MemoryRecall(store=memory))
        # Sandbox tools
        registry = registry.register(CodeRun())
        registry = registry.register(ShellExec())
        registry = registry.register(CodeInterpret())
        registry = registry.register(FileRead())
        registry = registry.register(FileWrite())
        registry = registry.register(FileEdit())
        registry = registry.register(FileList())
        registry = registry.register(PackageInstall())
        return registry

    return factory


def _build_orchestrator(
    event_emitter: EventEmitter,
    sandbox_provider: SandboxProvider,
    storage_backend: StorageBackend | None = None,
    initial_messages: tuple[dict[str, Any], ...] = (),
) -> tuple[AgentOrchestrator, ToolExecutor]:
    """Build an AgentOrchestrator using a callback holder to avoid two-phase construction."""
    settings = get_settings()
    client = _build_claude_client()
    callback_holder = _CallbackHolder()

    artifact_manager = ArtifactManager(storage_backend=storage_backend)
    registry = _build_base_registry(event_emitter, callback_holder, artifact_manager)
    executor = ToolExecutor(
        registry=registry,
        sandbox_provider=sandbox_provider,
        event_emitter=event_emitter,
        artifact_manager=artifact_manager,
    )

    orchestrator = AgentOrchestrator(
        claude_client=client,
        tool_registry=registry,
        tool_executor=executor,
        event_emitter=event_emitter,
        system_prompt=settings.DEFAULT_SYSTEM_PROMPT,
        max_iterations=settings.MAX_ITERATIONS,
        initial_messages=initial_messages,
    )
    callback_holder.set(orchestrator.on_task_complete)

    return orchestrator, executor


def _build_planner_orchestrator(
    event_emitter: EventEmitter,
    sandbox_provider: SandboxProvider,
    storage_backend: StorageBackend | None = None,
) -> tuple[PlannerOrchestrator, ToolExecutor]:
    """Build a PlannerOrchestrator with properly wired sub-agent registries."""
    settings = get_settings()
    client = _build_claude_client()
    callback_holder = _CallbackHolder()

    sub_agent_manager = SubAgentManager(
        claude_client=client,
        tool_registry_factory=_build_sub_agent_registry_factory(
            event_emitter, sandbox_provider
        ),
        tool_executor_factory=lambda reg: ToolExecutor(
            registry=reg,
            sandbox_provider=sandbox_provider,
            event_emitter=event_emitter,
        ),
        event_emitter=event_emitter,
    )

    artifact_manager = ArtifactManager(storage_backend=storage_backend)
    base_registry = _build_base_registry(
        event_emitter, callback_holder, artifact_manager
    )
    executor = ToolExecutor(
        registry=base_registry,
        sandbox_provider=sandbox_provider,
        event_emitter=event_emitter,
        artifact_manager=artifact_manager,
    )

    orchestrator = PlannerOrchestrator(
        claude_client=client,
        tool_registry=base_registry,
        tool_executor=executor,
        event_emitter=event_emitter,
        sub_agent_manager=sub_agent_manager,
        max_iterations=settings.MAX_ITERATIONS,
    )
    callback_holder.set(orchestrator.on_task_complete)

    return orchestrator, orchestrator._executor


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------


def _create_queue_subscriber(
    queue: asyncio.Queue[AgentEvent | None],
    pending_callbacks: dict[str, Any],
) -> Any:
    """Create an async callback that pushes events into a queue."""

    async def _subscriber(event: AgentEvent) -> None:
        callback = event.data.get("response_callback")
        if callback is not None:
            request_id = f"req_{uuid.uuid4().hex[:12]}"
            event = AgentEvent(
                type=event.type,
                data={**event.data, "_request_id": request_id},
                timestamp=event.timestamp,
                iteration=event.iteration,
            )
            pending_callbacks[request_id] = callback
        await queue.put(event)

    return _subscriber


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def _create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from agent.logging import setup_logging

    settings = get_settings()
    setup_logging(log_level=settings.LOG_LEVEL)
    @asynccontextmanager
    async def _lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
        await init_db(db_engine)
        asyncio.create_task(_cleanup_stale_conversations())
        yield
        # Wait for in-flight DB writes before tearing down connections
        logger.info("shutdown_draining_pending_writes count={}", db_pending_writes.count)
        await db_pending_writes.wait_drained(timeout=5.0)
        if sandbox_pool is not None:
            logger.info("Draining sandbox pool on shutdown")
            await sandbox_pool.drain()
        await db_engine.dispose()
        logger.info("database_engine_disposed")

    application = FastAPI(title="HiAgent", version="0.1.0", lifespan=_lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create sandbox provider once at app startup (shared across conversations)
    sandbox_provider, sandbox_pool = _build_sandbox_provider()

    # Create shared storage backend (local or R2)
    storage_backend = create_storage_backend(settings)

    # Database setup
    settings_db = get_settings()
    db_engine = get_engine(settings_db.DATABASE_URL)
    db_session_factory = get_session_factory(db_engine)
    db_repo = ConversationRepository()
    db_pending_writes = PendingWrites()

    # FastAPI dependency for DB sessions
    async def _get_db_session():
        async for session in get_session(db_session_factory):
            yield session

    # Common dependencies for all endpoints
    _deps = [Depends(_verify_api_key), Depends(_check_rate_limit)]

    @application.post(
        "/conversations",
        response_model=ConversationResponse,
        dependencies=_deps,
    )
    async def create_conversation(request: MessageRequest) -> ConversationResponse:
        """Create a new conversation and send the first message."""
        conversation_id = str(uuid.uuid4())
        emitter = EventEmitter()

        event_queue: asyncio.Queue[AgentEvent | None] = asyncio.Queue(
            maxsize=_EVENT_QUEUE_MAXSIZE,
        )
        pending_callbacks: dict[str, Any] = {}
        subscriber = _create_queue_subscriber(event_queue, pending_callbacks)
        emitter.subscribe(subscriber)

        orchestrator: Runnable
        executor: ToolExecutor
        if request.use_planner:
            orchestrator, executor = _build_planner_orchestrator(
                emitter, sandbox_provider, storage_backend
            )
        else:
            orchestrator, executor = _build_orchestrator(
                emitter, sandbox_provider, storage_backend
            )

        entry = ConversationEntry(
            emitter=emitter,
            event_queue=event_queue,
            orchestrator=orchestrator,
            executor=executor,
            pending_callbacks=pending_callbacks,
        )
        entry.subscriber = subscriber
        _conversations[conversation_id] = entry

        # Persist conversation and register DB subscriber
        conv_uuid = uuid.UUID(conversation_id)
        async with db_session_factory() as session:
            await db_repo.create_conversation(
                session, title=request.message[:80], conversation_id=conv_uuid
            )
        db_sub = create_db_subscriber(conv_uuid, db_repo, db_session_factory, db_pending_writes)
        emitter.subscribe(db_sub)

        # Start first turn
        entry.turn_task = asyncio.create_task(
            _run_turn(conversation_id, orchestrator, request.message),
        )

        # Generate a concise title in the background
        asyncio.create_task(
            _generate_title(conversation_id, request.message, emitter),
        )

        logger.info("conversation_created id=%s", conversation_id)
        return ConversationResponse(conversation_id=conversation_id)

    async def _reconstruct_conversation(
        conversation_id: str,
    ) -> ConversationEntry | None:
        """Reconstruct a conversation from DB history when it's been evicted from memory.

        Returns the new ConversationEntry, or None if the conversation doesn't exist in DB.
        """
        conv_uuid = uuid.UUID(conversation_id)
        async with db_session_factory() as session:
            convo = await db_repo.get_conversation(session, conv_uuid)
            if convo is None:
                return None
            db_messages = await db_repo.get_messages(session, conv_uuid)

        # Convert DB messages to Claude API format
        initial_messages: list[dict[str, Any]] = []
        for m in db_messages:
            if m.role not in ("user", "assistant"):
                continue
            content = m.content
            if isinstance(content, dict) and "text" in content:
                text = content["text"]
            elif isinstance(content, str):
                text = content
            else:
                text = str(content)
            initial_messages.append({"role": m.role, "content": text})

        emitter = EventEmitter()
        event_queue: asyncio.Queue[AgentEvent | None] = asyncio.Queue(
            maxsize=_EVENT_QUEUE_MAXSIZE,
        )
        pending_callbacks: dict[str, Any] = {}
        subscriber = _create_queue_subscriber(event_queue, pending_callbacks)
        emitter.subscribe(subscriber)

        orchestrator, executor = _build_orchestrator(
            emitter,
            sandbox_provider,
            storage_backend,
            initial_messages=tuple(initial_messages),
        )

        entry = ConversationEntry(
            emitter=emitter,
            event_queue=event_queue,
            orchestrator=orchestrator,
            executor=executor,
            pending_callbacks=pending_callbacks,
        )
        entry.subscriber = subscriber
        _conversations[conversation_id] = entry

        # Re-register DB subscriber for new events
        db_sub = create_db_subscriber(conv_uuid, db_repo, db_session_factory, db_pending_writes)
        emitter.subscribe(db_sub)

        logger.info(
            "conversation_reconstructed id=%s messages=%d",
            conversation_id,
            len(initial_messages),
        )
        return entry

    @application.post(
        "/conversations/{conversation_id}/messages",
        response_model=ConversationResponse,
        dependencies=_deps,
    )
    async def send_message(
        conversation_id: str = Path(..., pattern=_UUID_PATTERN),
        request: MessageRequest = ...,  # type: ignore[assignment]
    ) -> ConversationResponse:
        """Send a follow-up message in an existing conversation."""
        entry = _conversations.get(conversation_id)
        if entry is None:
            entry = await _reconstruct_conversation(conversation_id)
            if entry is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Unknown conversation: {conversation_id}",
                )

        # Wait for any in-progress turn to finish before starting the next
        if entry.turn_task is not None and not entry.turn_task.done():
            await entry.turn_task

        # Start new turn on the same orchestrator (preserves full history)
        entry.turn_task = asyncio.create_task(
            _run_turn(conversation_id, entry.orchestrator, request.message),
        )

        # Touch updated_at timestamp
        try:
            async with db_session_factory() as session:
                await db_repo.update_conversation(
                    session, uuid.UUID(conversation_id)
                )
        except Exception:
            logger.warning(
                "failed_to_update_conversation_timestamp id=%s", conversation_id
            )

        logger.info("message_sent conversation_id=%s", conversation_id)
        return ConversationResponse(conversation_id=conversation_id)

    @application.get(
        "/conversations/{conversation_id}/events",
        dependencies=_deps,
    )
    async def stream_events(
        conversation_id: str = Path(..., pattern=_UUID_PATTERN),
    ) -> StreamingResponse:
        """Stream conversation events via Server-Sent Events (long-lived)."""
        entry = _conversations.get(conversation_id)
        if entry is None:
            entry = await _reconstruct_conversation(conversation_id)
            if entry is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Unknown conversation: {conversation_id}",
                )

        return StreamingResponse(
            _event_generator(conversation_id, entry),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @application.post(
        "/conversations/{conversation_id}/respond",
        dependencies=_deps,
    )
    async def respond_to_prompt(
        body: UserInputRequest,
        conversation_id: str = Path(..., pattern=_UUID_PATTERN),
    ) -> dict[str, str]:
        """Submit a user response to an ask_user prompt."""
        entry = _conversations.get(conversation_id)
        if entry is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown conversation: {conversation_id}",
            )

        callback = entry.pending_callbacks.pop(body.request_id, None)
        if callback is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown request: {body.request_id}",
            )

        logger.info(
            "user_response_received conversation_id=%s request_id=%s",
            conversation_id,
            body.request_id,
        )
        callback(body.response)
        return {"status": "ok"}

    @application.delete(
        "/conversations/{conversation_id}",
        dependencies=_deps,
    )
    async def delete_conversation(
        conversation_id: str = Path(..., pattern=_UUID_PATTERN),
        session: Any = Depends(_get_db_session),
    ) -> dict[str, str]:
        """Delete a conversation and clean up in-memory resources."""
        await _cleanup_conversation(conversation_id)
        deleted = await db_repo.delete_conversation(session, uuid.UUID(conversation_id))
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")
        logger.info("conversation_deleted id=%s", conversation_id)
        return {"status": "ok"}

    @application.get("/conversations", dependencies=_deps)
    async def list_conversations(
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
        session: Any = Depends(_get_db_session),
    ) -> dict[str, Any]:
        """List conversations, paginated, newest first."""
        if limit > 100:
            limit = 100
        items, total = await db_repo.list_conversations(
            session, limit=limit, offset=offset, search=search
        )
        return {
            "items": [
                {
                    "id": str(item.id),
                    "title": item.title,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                }
                for item in items
            ],
            "total": total,
        }

    @application.get(
        "/conversations/{conversation_id}/messages",
        dependencies=_deps,
    )
    async def get_conversation_messages(
        conversation_id: str = Path(..., pattern=_UUID_PATTERN),
        session: Any = Depends(_get_db_session),
    ) -> dict[str, Any]:
        """Get all messages for a conversation (for history replay)."""
        conv_uuid = uuid.UUID(conversation_id)
        convo = await db_repo.get_conversation(session, conv_uuid)
        if convo is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        messages = await db_repo.get_messages(session, conv_uuid)
        return {
            "conversation_id": str(convo.id),
            "title": convo.title,
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "iteration": m.iteration,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
        }

    @application.get(
        "/conversations/{conversation_id}/events/history",
        dependencies=_deps,
    )
    async def get_conversation_events(
        conversation_id: str = Path(..., pattern=_UUID_PATTERN),
        session: Any = Depends(_get_db_session),
    ) -> dict[str, Any]:
        """Return all stored events for a historical conversation."""
        conv_uuid = uuid.UUID(conversation_id)
        convo = await db_repo.get_conversation(session, conv_uuid)
        if convo is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        events = await db_repo.get_events(session, conv_uuid)
        return {
            "events": [
                {
                    "type": event.event_type,
                    "data": event.data,
                    "timestamp": event.timestamp.isoformat(),
                    "iteration": event.iteration,
                }
                for event in events
            ],
        }

    @application.get(
        "/conversations/{conversation_id}/artifacts/{artifact_id}",
        dependencies=_deps,
        response_model=None,
    )
    async def get_artifact(
        conversation_id: str = Path(..., pattern=_UUID_PATTERN),
        artifact_id: str = Path(..., pattern=r"^[0-9a-f]{32}$"),
        session: Any = Depends(_get_db_session),
    ) -> FileResponse | RedirectResponse:
        """Serve an artifact file.

        Looks up artifact metadata from the database, then delegates
        to the storage backend (local file or R2 presigned URL).
        """
        record = await db_repo.get_artifact(session, artifact_id)
        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"Artifact not found: {artifact_id}",
            )

        # Local storage: serve the file directly
        if isinstance(storage_backend, LocalStorageBackend):
            file_path = await storage_backend.get_url(
                record.storage_key, record.content_type, record.original_name
            )
            if not os.path.isfile(file_path):
                raise HTTPException(
                    status_code=404,
                    detail="Artifact file not found on disk",
                )
            return FileResponse(
                path=file_path,
                media_type=record.content_type,
                filename=record.original_name,
            )

        # Remote storage (R2): redirect to presigned URL
        url = await storage_backend.get_url(
            record.storage_key, record.content_type, record.original_name
        )
        return RedirectResponse(url=url, status_code=307)

    return application


# ---------------------------------------------------------------------------
# Turn execution
# ---------------------------------------------------------------------------


async def _run_turn(
    conversation_id: str,
    orchestrator: Runnable,
    message: str,
) -> str:
    """Run a single turn of the conversation. Does NOT close the SSE connection."""
    try:
        logger.info("turn_started conversation_id=%s", conversation_id)
        result = await orchestrator.run(message)
        logger.info("turn_completed conversation_id=%s", conversation_id)
        return result
    except Exception:
        logger.exception("turn_failed conversation_id=%s", conversation_id)
        # Emit error event so the frontend is notified (C4 fix)
        entry = _conversations.get(conversation_id)
        if entry is not None:
            await entry.emitter.emit(
                EventType.TASK_ERROR,
                {"error": "An internal error occurred. Please try again."},
            )
        return "Error: An internal error occurred."


# ---------------------------------------------------------------------------
# SSE generator & cleanup
# ---------------------------------------------------------------------------


async def _event_generator(
    conversation_id: str,
    entry: ConversationEntry,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted events. Connection stays open between turns.

    When the SSE client disconnects we only detach the queue subscriber —
    the conversation itself is kept alive so the client can reconnect and
    send follow-up messages.  Actual cleanup happens via the stale-
    conversation reaper or an explicit DELETE.
    """
    try:
        while True:
            # Wait for next event (blocks between turns — that's intentional)
            try:
                event = await asyncio.wait_for(entry.event_queue.get(), timeout=300.0)
            except asyncio.TimeoutError:
                # Send keepalive comment to prevent proxy/browser timeout
                yield ": keepalive\n\n"
                continue

            if event is None:
                # Explicit conversation end
                yield "event: done\ndata: {}\n\n"
                break

            payload = _serialize_event(event)
            if event.type == EventType.ASK_USER:
                logger.info("sse_sending_ask_user payload=%s", payload[:200])
            yield f"event: {event.type.value}\ndata: {payload}\n\n"
    except (asyncio.CancelledError, GeneratorExit):
        logger.info("sse_client_disconnected conversation_id=%s", conversation_id)


async def _cleanup_conversation(conversation_id: str) -> None:
    """Clean up conversation resources when SSE connection closes."""
    entry = _conversations.pop(conversation_id, None)
    if entry is None:
        return

    if entry.subscriber is not None:
        entry.emitter.unsubscribe(entry.subscriber)

    # Cancel any running turn
    if entry.turn_task is not None and not entry.turn_task.done():
        entry.turn_task.cancel()

    # Cleanup executor (sandbox, etc.)
    try:
        await entry.executor.cleanup()
    except Exception as exc:
        logger.error(
            "cleanup_failed conversation_id=%s error=%s", conversation_id, str(exc)
        )

    # Drain remaining events
    while not entry.event_queue.empty():
        try:
            entry.event_queue.get_nowait()
        except asyncio.QueueEmpty:
            break

    logger.info("conversation_cleaned_up conversation_id=%s", conversation_id)


async def _cleanup_stale_conversations() -> None:
    """Periodically remove conversations that have been idle too long (H2 fix)."""
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        now = _time.monotonic()
        stale_ids: list[str] = []
        for cid, entry in _conversations.items():
            age = now - entry.created_at
            if age > _CONVERSATION_TTL_SECONDS:
                # Only clean up if the turn is done and queue is drained
                if entry.turn_task is None or entry.turn_task.done():
                    stale_ids.append(cid)
        for cid in stale_ids:
            logger.info("cleaning_stale_conversation id=%s", cid)
            await _cleanup_conversation(cid)


async def _generate_title(
    conversation_id: str,
    user_message: str,
    emitter: EventEmitter,
) -> None:
    """Generate a short conversation title using the lite model."""
    try:
        settings = get_settings()
        client = ClaudeClient(
            api_key=settings.ANTHROPIC_API_KEY,
            default_model=settings.LITE_MODEL,
            base_url=settings.ANTHROPIC_BASE_URL,
        )
        response = await client.create_message(
            system=(
                "Generate a concise title (max 50 chars) for this conversation. "
                "Reply with ONLY the title, no quotes or punctuation."
            ),
            messages=[{"role": "user", "content": user_message}],
            max_tokens=30,
        )
        title = response.text.strip()[:80]
        await emitter.emit(EventType.CONVERSATION_TITLE, {"title": title})
    except Exception:
        logger.warning("title_generation_failed conversation_id=%s", conversation_id)


def _serialize_event(event: AgentEvent) -> str:
    """Serialize an AgentEvent to a JSON string."""
    serializable_data: dict[str, Any] = {}
    for k, v in event.data.items():
        if k == "_request_id":
            serializable_data["request_id"] = v
        elif callable(v):
            continue
        else:
            serializable_data[k] = v

    return json.dumps(
        {
            "event_type": event.type.value,
            "data": serializable_data,
            "timestamp": event.timestamp,
            "iteration": event.iteration,
        },
        default=str,
    )


app = _create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )

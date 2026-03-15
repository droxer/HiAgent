"""FastAPI application with SSE streaming for conversation-based agent."""

from __future__ import annotations

import asyncio
import json
import time as _time
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator, Callable
from typing import Any, Protocol

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

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
from loguru import logger

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
    """Enforce per-IP rate limiting."""
    global _rate_limiter  # noqa: PLW0603
    if _rate_limiter is None:
        settings = get_settings()
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
        max_tokens=settings.MAX_TOKENS,
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
) -> tuple[AgentOrchestrator, ToolExecutor]:
    """Build an AgentOrchestrator using a callback holder to avoid two-phase construction."""
    settings = get_settings()
    client = _build_claude_client()
    callback_holder = _CallbackHolder()

    registry = _build_base_registry(event_emitter, callback_holder)
    executor = ToolExecutor(
        registry=registry,
        sandbox_provider=sandbox_provider,
        event_emitter=event_emitter,
    )

    orchestrator = AgentOrchestrator(
        claude_client=client,
        tool_registry=registry,
        tool_executor=executor,
        event_emitter=event_emitter,
        system_prompt=settings.DEFAULT_SYSTEM_PROMPT,
        max_iterations=settings.MAX_ITERATIONS,
    )
    callback_holder.set(orchestrator.on_task_complete)

    return orchestrator, executor


def _build_planner_orchestrator(
    event_emitter: EventEmitter,
    sandbox_provider: SandboxProvider,
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

    base_registry = _build_base_registry(event_emitter, callback_holder)
    executor = ToolExecutor(
        registry=base_registry,
        sandbox_provider=sandbox_provider,
        event_emitter=event_emitter,
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
    application = FastAPI(title="HiAgent", version="0.1.0")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create sandbox provider once at app startup (shared across conversations)
    sandbox_provider, sandbox_pool = _build_sandbox_provider()

    # Common dependencies for all endpoints
    _deps = [Depends(_verify_api_key), Depends(_check_rate_limit)]

    @application.on_event("startup")
    async def _start_cleanup_task() -> None:
        asyncio.create_task(_cleanup_stale_conversations())

    @application.on_event("shutdown")
    async def _drain_sandbox_pool() -> None:
        if sandbox_pool is not None:
            logger.info("Draining sandbox pool on shutdown")
            await sandbox_pool.drain()

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
                emitter, sandbox_provider
            )
        else:
            orchestrator, executor = _build_orchestrator(emitter, sandbox_provider)

        entry = ConversationEntry(
            emitter=emitter,
            event_queue=event_queue,
            orchestrator=orchestrator,
            executor=executor,
            pending_callbacks=pending_callbacks,
        )
        entry.subscriber = subscriber
        _conversations[conversation_id] = entry

        # Start first turn
        entry.turn_task = asyncio.create_task(
            _run_turn(conversation_id, orchestrator, request.message),
        )

        logger.info("conversation_created id=%s", conversation_id)
        return ConversationResponse(conversation_id=conversation_id)

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
    """Yield SSE-formatted events. Connection stays open between turns."""
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
            yield f"event: {event.type.value}\ndata: {payload}\n\n"
    except (asyncio.CancelledError, GeneratorExit):
        logger.info("sse_client_disconnected conversation_id=%s", conversation_id)
    finally:
        # Cleanup on disconnect
        await _cleanup_conversation(conversation_id)


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

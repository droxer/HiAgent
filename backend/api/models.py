"""Shared models, protocols, and constants for the API layer."""

from __future__ import annotations

import asyncio
import time as _time
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import BaseModel, Field, field_validator

from agent.mcp.client import MCPStdioClient
from agent.mcp.config import MCPServerConfig
from agent.tools.executor import ToolExecutor
from agent.tools.registry import ToolRegistry
from api.events import AgentEvent, EventEmitter

# UUID pattern for path parameter validation
_UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

# Max event queue size for backpressure
_EVENT_QUEUE_MAXSIZE = 5000

# Stale conversation TTL in seconds (1 hour)
_CONVERSATION_TTL_SECONDS = 3600

# Default port for sandbox preview proxy
_DEFAULT_PREVIEW_PORT = 8080

# File upload constraints
MAX_FILE_SIZE_MB = 25
MAX_FILES_PER_MESSAGE = 10
VISION_MIME_TYPES = frozenset({
    "image/png", "image/jpeg", "image/gif", "image/webp",
    "application/pdf",
})


@dataclass(frozen=True)
class FileAttachment:
    """Immutable representation of an uploaded file."""

    filename: str
    content_type: str
    data: bytes
    size: int


class Runnable(Protocol):
    """Protocol for orchestrators that can run a turn."""

    async def run(
        self,
        user_message: str,
        attachments: tuple[FileAttachment, ...] = (),
        selected_skills: tuple[str, ...] = (),
    ) -> str: ...


class Cancellable(Protocol):
    """Protocol for orchestrators that support cancellation and retry."""

    def cancel(self) -> None: ...

    def reset_cancel(self) -> None: ...

    def get_last_user_message(self) -> str | None: ...

    def rollback_to_before_last_user_message(self) -> None: ...


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
        "last_attachments",
        "last_selected_skills",
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
        self.last_attachments: tuple[FileAttachment, ...] = ()
        self.last_selected_skills: tuple[str, ...] = ()


@dataclass
class MCPState:
    """Container for MCP lifecycle state, stored on app.state."""

    registry: ToolRegistry | None = None
    clients: dict[str, MCPStdioClient] = field(default_factory=dict)
    configs: dict[str, MCPServerConfig] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class MessageRequest(BaseModel):
    """Request body for creating a conversation or sending a message."""

    message: str = Field(max_length=100_000)
    skills: list[str] = Field(default_factory=list)
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


class MCPServerResponse(BaseModel):
    """Response model for a single MCP server."""

    name: str
    transport: str
    command: str = ""
    url: str = ""
    status: str  # "connected" | "disconnected"
    tool_count: int = 0


class MCPServerCreateRequest(BaseModel):
    """Request body for adding a new MCP server."""

    name: str = Field(max_length=100)
    transport: str
    command: str = ""
    args: list[str] = Field(default_factory=list)
    url: str = ""
    env: dict[str, str] = Field(default_factory=dict)
    timeout: float = 30.0

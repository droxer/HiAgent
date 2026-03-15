"""SQLite-backed task history data models.

Frozen dataclasses representing records stored in the SQLite
database. These are pure data containers with no behavior —
all persistence logic lives in ``repository.py``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskRecord:
    """Immutable record of a submitted task.

    Attributes:
        id: Unique task identifier.
        message: The original user message / task description.
        status: Current status (e.g. "pending", "running", "completed", "failed").
        result: Final result text, if available.
        created_at: Unix timestamp when the task was created.
        completed_at: Unix timestamp when the task finished, if applicable.
    """

    id: str
    message: str
    status: str
    result: str | None
    created_at: float
    completed_at: float | None


@dataclass(frozen=True)
class AgentRunRecord:
    """Immutable record of a single agent run within a task.

    Attributes:
        id: Unique run identifier.
        task_id: ID of the parent task.
        config_json: Serialized agent configuration.
        status: Current run status.
        result_json: Serialized result data, if available.
        created_at: Unix timestamp when the run started.
    """

    id: str
    task_id: str
    config_json: str
    status: str
    result_json: str | None
    created_at: float


@dataclass(frozen=True)
class EventRecord:
    """Immutable record of an event emitted during task execution.

    Attributes:
        id: Auto-incremented event identifier.
        task_id: ID of the parent task.
        event_type: Type of event (matches ``EventType`` values).
        data_json: Serialized event payload.
        timestamp: Unix timestamp when the event was emitted.
    """

    id: int
    task_id: str
    event_type: str
    data_json: str
    timestamp: float

"""SQLite repository for task history CRUD operations.

Uses ``asyncio.to_thread`` to wrap synchronous sqlite3 calls,
keeping the event loop responsive. All returned records are
frozen dataclasses — no mutation is possible through this API.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time

from agent.state.models import EventRecord, TaskRecord
from api.events import AgentEvent

# ---------------------------------------------------------------------------
# SQL constants
# ---------------------------------------------------------------------------

_CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    result TEXT,
    created_at REAL NOT NULL,
    completed_at REAL
)
"""

_CREATE_AGENT_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    config_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    result_json TEXT,
    created_at REAL NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
)
"""

_CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    data_json TEXT NOT NULL,
    timestamp REAL NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
)
"""


# ---------------------------------------------------------------------------
# Pure row-to-record converters
# ---------------------------------------------------------------------------


def _row_to_task(row: sqlite3.Row) -> TaskRecord:
    """Convert a database row to a ``TaskRecord``."""
    return TaskRecord(
        id=row["id"],
        message=row["message"],
        status=row["status"],
        result=row["result"],
        created_at=row["created_at"],
        completed_at=row["completed_at"],
    )


def _row_to_event(row: sqlite3.Row) -> EventRecord:
    """Convert a database row to an ``EventRecord``."""
    return EventRecord(
        id=row["id"],
        task_id=row["task_id"],
        event_type=row["event_type"],
        data_json=row["data_json"],
        timestamp=row["timestamp"],
    )


# ---------------------------------------------------------------------------
# Synchronous database helpers (run via asyncio.to_thread)
# ---------------------------------------------------------------------------


def _open_connection(db_path: str) -> sqlite3.Connection:
    """Open a sqlite3 connection with row factory and WAL mode enabled."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _ensure_tables_sync(conn: sqlite3.Connection) -> None:
    """Create tables if they do not already exist."""
    conn.execute(_CREATE_TASKS_TABLE)
    conn.execute(_CREATE_AGENT_RUNS_TABLE)
    conn.execute(_CREATE_EVENTS_TABLE)
    conn.commit()


def _create_task_sync(
    conn: sqlite3.Connection, task_id: str, message: str
) -> TaskRecord:
    """Insert a new task and return its record."""
    now = time.time()
    conn.execute(
        "INSERT INTO tasks (id, message, status, created_at) VALUES (?, ?, ?, ?)",
        (task_id, message, "pending", now),
    )
    conn.commit()
    return TaskRecord(
        id=task_id,
        message=message,
        status="pending",
        result=None,
        created_at=now,
        completed_at=None,
    )


def _update_task_sync(
    conn: sqlite3.Connection,
    task_id: str,
    status: str,
    result: str | None,
) -> TaskRecord:
    """Update a task's status and optional result, returning the new record."""
    completed_at = time.time() if status in ("completed", "failed") else None
    conn.execute(
        "UPDATE tasks SET status=?, result=?, completed_at=? WHERE id=?",
        (status, result, completed_at, task_id),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM tasks WHERE id=?",
        (task_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Task not found: {task_id}")
    return _row_to_task(row)


def _get_task_sync(conn: sqlite3.Connection, task_id: str) -> TaskRecord | None:
    """Fetch a single task by ID."""
    row = conn.execute(
        "SELECT * FROM tasks WHERE id=?",
        (task_id,),
    ).fetchone()
    return _row_to_task(row) if row else None


def _list_tasks_sync(conn: sqlite3.Connection, limit: int) -> tuple[TaskRecord, ...]:
    """List recent tasks ordered by creation time (newest first)."""
    rows = conn.execute(
        "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return tuple(_row_to_task(row) for row in rows)


def _save_event_sync(
    conn: sqlite3.Connection,
    task_id: str,
    event: AgentEvent,
) -> None:
    """Persist an agent event to the events table."""
    data_json = json.dumps(event.data, default=str)
    conn.execute(
        "INSERT INTO events (task_id, event_type, data_json, timestamp) "
        "VALUES (?, ?, ?, ?)",
        (task_id, str(event.type), data_json, event.timestamp),
    )
    conn.commit()


def _get_events_sync(conn: sqlite3.Connection, task_id: str) -> tuple[EventRecord, ...]:
    """Fetch all events for a task ordered by timestamp."""
    rows = conn.execute(
        "SELECT * FROM events WHERE task_id=? ORDER BY timestamp ASC",
        (task_id,),
    ).fetchall()
    return tuple(_row_to_event(row) for row in rows)


# ---------------------------------------------------------------------------
# TaskRepository (async facade)
# ---------------------------------------------------------------------------


class TaskRepository:
    """Async repository for task history backed by SQLite.

    Maintains a single long-lived connection per instance, initialised lazily
    on first use.  All database operations run in a thread pool via
    ``asyncio.to_thread`` to avoid blocking the event loop.  Returned records
    are frozen dataclasses — no mutation is possible through this API.

    Call ``close()`` when the repository is no longer needed to release the
    underlying database connection.
    """

    def __init__(self, db_path: str = "./hiagent.db") -> None:
        if not db_path:
            raise ValueError("db_path must not be empty")
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        """Return the shared connection, opening it if necessary (sync)."""
        if self._conn is None:
            self._conn = _open_connection(self._db_path)
            _ensure_tables_sync(self._conn)
        return self._conn

    async def _run(self, fn, *args):  # type: ignore[no-untyped-def]
        """Execute a synchronous DB helper in a thread, passing the shared connection."""
        return await asyncio.to_thread(fn, self._get_conn(), *args)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_task(self, task_id: str, message: str) -> TaskRecord:
        """Create a new task record.

        Args:
            task_id: Unique identifier for the task.
            message: The user's task description.

        Returns:
            The newly created ``TaskRecord``.
        """
        return await self._run(_create_task_sync, task_id, message)

    async def update_task(
        self,
        task_id: str,
        status: str,
        result: str | None = None,
    ) -> TaskRecord:
        """Update a task's status and optional result.

        Args:
            task_id: The task to update.
            status: New status value.
            result: Optional result text.

        Returns:
            The updated ``TaskRecord``.

        Raises:
            ValueError: If the task does not exist.
        """
        return await self._run(_update_task_sync, task_id, status, result)

    async def get_task(self, task_id: str) -> TaskRecord | None:
        """Fetch a task by ID, returning None if not found."""
        return await self._run(_get_task_sync, task_id)

    async def list_tasks(self, limit: int = 50) -> tuple[TaskRecord, ...]:
        """List recent tasks, newest first.

        Args:
            limit: Maximum number of tasks to return.
        """
        return await self._run(_list_tasks_sync, limit)

    async def save_event(self, task_id: str, event: AgentEvent) -> None:
        """Persist an ``AgentEvent`` to the database.

        Args:
            task_id: The task this event belongs to.
            event: The event to save.
        """
        await self._run(_save_event_sync, task_id, event)

    async def get_events(self, task_id: str) -> tuple[EventRecord, ...]:
        """Fetch all events for a task, ordered by timestamp.

        Args:
            task_id: The task whose events to retrieve.
        """
        return await self._run(_get_events_sync, task_id)

    def close(self) -> None:
        """Close the underlying SQLite connection.

        Safe to call multiple times; subsequent calls are no-ops.
        """
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None

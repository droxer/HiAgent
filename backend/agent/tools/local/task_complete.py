"""Tool to signal that the agent has completed its task."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from agent.tools.base import (
    ExecutionContext,
    LocalTool,
    ToolDefinition,
    ToolResult,
)


class TaskComplete(LocalTool):
    """Signal that the current task is complete."""

    def __init__(self, on_complete: Callable[[str], Coroutine[Any, Any, None]]) -> None:
        if on_complete is None:
            raise ValueError("Completion callback must not be None")
        self._on_complete = on_complete

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="task_complete",
            description="Signal that the task is complete and provide a summary.",
            input_schema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "A summary of what was accomplished.",
                    },
                },
                "required": ["summary"],
            },
            execution_context=ExecutionContext.LOCAL,
            tags=("control",),
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        summary: str = kwargs.get("summary", "")

        if not summary.strip():
            return ToolResult.fail("Summary must not be empty")

        try:
            await self._on_complete(summary)
        except Exception as exc:
            return ToolResult.fail(f"Failed to complete task: {exc}")

        return ToolResult.ok("Task marked as complete.")

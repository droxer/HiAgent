"""Tool for asking the user a question and waiting for a response."""

from __future__ import annotations

from typing import Any

from agent.tools.base import (
    ExecutionContext,
    LocalTool,
    ToolDefinition,
    ToolResult,
)
from api.events import EventType


class AskUser(LocalTool):
    """Ask the user a question and block until they respond."""

    def __init__(self, event_emitter: Any) -> None:
        if event_emitter is None:
            raise ValueError("EventEmitter must not be None")
        self._emitter = event_emitter

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="user_ask",
            description="Ask the user a question and wait for their response.",
            input_schema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask the user.",
                    },
                },
                "required": ["question"],
            },
            execution_context=ExecutionContext.LOCAL,
            tags=("communication",),
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        question: str = kwargs.get("question", "")

        if not question.strip():
            return ToolResult.fail("Question must not be empty")

        try:
            response = await self._emitter.emit_and_wait(
                EventType.ASK_USER, {"question": question}
            )
        except Exception as exc:
            return ToolResult.fail(f"Failed to get user response: {exc}")

        return ToolResult.ok(response)

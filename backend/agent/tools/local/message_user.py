"""Tool for sending messages to the user via the event system."""

from __future__ import annotations

from typing import Any

from agent.tools.base import (
    ExecutionContext,
    LocalTool,
    ToolDefinition,
    ToolResult,
)
from api.events import EventType


class MessageUser(LocalTool):
    """Send a message to the user without expecting a reply."""

    def __init__(self, event_emitter: Any) -> None:
        if event_emitter is None:
            raise ValueError("EventEmitter must not be None")
        self._emitter = event_emitter

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="message_user",
            description="Send a message to the user.",
            input_schema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to send to the user.",
                    },
                },
                "required": ["message"],
            },
            execution_context=ExecutionContext.LOCAL,
            tags=("communication",),
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        message: str = kwargs.get("message", "")

        if not message.strip():
            return ToolResult.fail("Message must not be empty")

        try:
            await self._emitter.emit(EventType.MESSAGE_USER, {"message": message})
        except Exception as exc:
            return ToolResult.fail(f"Failed to send message: {exc}")

        return ToolResult.ok("Message sent to user.")

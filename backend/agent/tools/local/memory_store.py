"""Tool for storing key-value pairs in shared memory."""

from __future__ import annotations

from typing import Any

from agent.tools.base import (
    ExecutionContext,
    LocalTool,
    ToolDefinition,
    ToolResult,
)


class MemoryStore(LocalTool):
    """Store a value in the agent's shared memory under a namespaced key."""

    def __init__(self, store: dict[str, str]) -> None:
        if store is None:
            raise ValueError("Store dict must not be None")
        self._store = store

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="memory_store",
            description="Store a key-value pair in the agent's memory.",
            input_schema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "The key to store the value under.",
                    },
                    "value": {
                        "type": "string",
                        "description": "The value to store.",
                    },
                    "namespace": {
                        "type": "string",
                        "description": "Namespace for grouping related entries.",
                        "default": "default",
                    },
                },
                "required": ["key", "value"],
            },
            execution_context=ExecutionContext.LOCAL,
            tags=("memory",),
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        key: str = kwargs.get("key", "")
        value: str = kwargs.get("value", "")
        namespace: str = kwargs.get("namespace", "default")

        if not key.strip():
            return ToolResult.fail("Key must not be empty")
        if not value:
            return ToolResult.fail("Value must not be empty")

        compound_key = f"{namespace}:{key}"
        self._store[compound_key] = value

        return ToolResult.ok(
            f"Stored value under '{compound_key}'.",
            metadata={"namespace": namespace, "key": key},
        )

"""Tool for recalling entries from shared memory by substring search."""

from __future__ import annotations

import json
from typing import Any

from agent.tools.base import (
    ExecutionContext,
    LocalTool,
    ToolDefinition,
    ToolResult,
)


class MemoryRecall(LocalTool):
    """Search the agent's shared memory for entries matching a query."""

    def __init__(self, store: dict[str, str]) -> None:
        if store is None:
            raise ValueError("Store dict must not be None")
        self._store = store

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="memory_recall",
            description="Search agent memory for entries matching a query string.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Substring to search for in keys and values.",
                    },
                    "namespace": {
                        "type": "string",
                        "description": "Namespace to search within.",
                        "default": "default",
                    },
                },
                "required": ["query"],
            },
            execution_context=ExecutionContext.LOCAL,
            tags=("memory",),
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        query: str = kwargs.get("query", "")
        namespace: str = kwargs.get("namespace", "default")

        if not query.strip():
            return ToolResult.fail("Query must not be empty")

        prefix = f"{namespace}:"
        query_lower = query.lower()

        matches = {
            k: v
            for k, v in self._store.items()
            if k.startswith(prefix)
            and (query_lower in k.lower() or query_lower in v.lower())
        }

        return ToolResult.ok(
            json.dumps(matches, ensure_ascii=False),
            metadata={"match_count": len(matches), "namespace": namespace},
        )

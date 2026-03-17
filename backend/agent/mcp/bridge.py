"""Bridge between MCP tools and HiAgent's tool system."""

from __future__ import annotations

from typing import Any

from agent.mcp.client import MCPCallResult, MCPStdioClient, MCPToolSchema
from agent.tools.base import ExecutionContext, LocalTool, ToolDefinition, ToolResult


class MCPBridgedTool(LocalTool):
    """A LocalTool that proxies calls to an MCP server.

    Each instance wraps a single MCP tool discovered from a server.
    The registered tool name is prefixed with the server name
    (``<server>__<tool>``) to avoid collisions across servers.
    """

    def __init__(self, schema: MCPToolSchema, client: MCPStdioClient) -> None:
        self._schema = schema
        self._client = client

    def definition(self) -> ToolDefinition:
        prefixed_name = f"{self._schema.server_name}__{self._schema.name}"
        return ToolDefinition(
            name=prefixed_name,
            description=self._schema.description,
            input_schema=self._schema.input_schema,
            execution_context=ExecutionContext.LOCAL,
            tags=("mcp", self._schema.server_name),
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        result: MCPCallResult = await self._client.call_tool(
            self._schema.name, kwargs
        )
        if result.is_error:
            return ToolResult.fail(result.content)
        return ToolResult.ok(
            result.content,
            metadata={"mcp_server": self._schema.server_name},
        )

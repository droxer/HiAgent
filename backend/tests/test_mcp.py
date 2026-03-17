"""Tests for MCP bridge, config, and client."""

from __future__ import annotations

import asyncio
import json
import types
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.mcp.client import MCPCallResult, MCPStdioClient, MCPToolSchema, MCP_PROTOCOL_VERSION
from agent.mcp.config import MCPServerConfig
from agent.mcp.bridge import MCPBridgedTool
from agent.tools.base import ExecutionContext
from agent.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# MCPServerConfig
# ---------------------------------------------------------------------------


class TestMCPServerConfig:
    def test_frozen(self) -> None:
        cfg = MCPServerConfig(name="test", transport="stdio", command="echo")
        assert cfg.name == "test"
        assert cfg.transport == "stdio"
        with pytest.raises(AttributeError):
            cfg.name = "other"  # type: ignore[misc]

    def test_defaults(self) -> None:
        cfg = MCPServerConfig(name="x", transport="stdio", command="echo")
        assert cfg.args == ()
        assert cfg.url == ""
        assert cfg.env == ()
        assert cfg.timeout == 30.0

    def test_invalid_transport_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported MCP transport"):
            MCPServerConfig(name="x", transport="websocket", command="echo")

    def test_stdio_requires_command(self) -> None:
        with pytest.raises(ValueError, match="stdio transport requires a command"):
            MCPServerConfig(name="x", transport="stdio")

    def test_sse_requires_url(self) -> None:
        with pytest.raises(ValueError, match="sse transport requires a url"):
            MCPServerConfig(name="x", transport="sse")

    def test_sse_valid(self) -> None:
        cfg = MCPServerConfig(name="x", transport="sse", url="http://localhost:8080")
        assert cfg.url == "http://localhost:8080"

    def test_custom_timeout(self) -> None:
        cfg = MCPServerConfig(name="x", transport="stdio", command="echo", timeout=60.0)
        assert cfg.timeout == 60.0


# ---------------------------------------------------------------------------
# MCPToolSchema
# ---------------------------------------------------------------------------


class TestMCPToolSchema:
    def test_frozen(self) -> None:
        schema = MCPToolSchema(
            name="test_tool",
            description="A test",
            input_schema=types.MappingProxyType({"type": "object"}),
            server_name="server1",
        )
        assert schema.name == "test_tool"

    def test_input_schema_immutable(self) -> None:
        schema = MCPToolSchema(
            name="test_tool",
            description="A test",
            input_schema=types.MappingProxyType({"type": "object", "properties": {}}),
            server_name="server1",
        )
        with pytest.raises(TypeError):
            schema.input_schema["type"] = "string"  # type: ignore[index]


# ---------------------------------------------------------------------------
# MCPCallResult
# ---------------------------------------------------------------------------


class TestMCPCallResult:
    def test_success(self) -> None:
        r = MCPCallResult(content="ok")
        assert not r.is_error

    def test_error(self) -> None:
        r = MCPCallResult(content="fail", is_error=True)
        assert r.is_error


# ---------------------------------------------------------------------------
# MCPBridgedTool
# ---------------------------------------------------------------------------


class TestMCPBridgedTool:
    def test_definition_has_prefixed_name(self) -> None:
        schema = MCPToolSchema(
            name="mcp_test",
            description="Test MCP tool",
            input_schema=types.MappingProxyType({"type": "object", "properties": {}}),
            server_name="test_server",
        )
        tool = MCPBridgedTool(schema, client=None)  # type: ignore[arg-type]
        defn = tool.definition()
        assert defn.name == "test_server__mcp_test"
        assert defn.execution_context == ExecutionContext.LOCAL
        assert "mcp" in defn.tags
        assert "test_server" in defn.tags

    @pytest.mark.asyncio
    async def test_execute_success(self) -> None:
        schema = MCPToolSchema(
            name="search",
            description="Search",
            input_schema=types.MappingProxyType({"type": "object"}),
            server_name="srv",
        )
        mock_client = AsyncMock(spec=MCPStdioClient)
        mock_client.call_tool.return_value = MCPCallResult(content="found it")

        tool = MCPBridgedTool(schema, mock_client)
        result = await tool.execute(query="test")

        mock_client.call_tool.assert_awaited_once_with("search", {"query": "test"})
        assert result.success
        assert result.output == "found it"

    @pytest.mark.asyncio
    async def test_execute_error(self) -> None:
        schema = MCPToolSchema(
            name="search",
            description="Search",
            input_schema=types.MappingProxyType({"type": "object"}),
            server_name="srv",
        )
        mock_client = AsyncMock(spec=MCPStdioClient)
        mock_client.call_tool.return_value = MCPCallResult(
            content="not found", is_error=True
        )

        tool = MCPBridgedTool(schema, mock_client)
        result = await tool.execute(query="test")

        assert not result.success
        assert result.error == "not found"


# ---------------------------------------------------------------------------
# MCPStdioClient
# ---------------------------------------------------------------------------


def _make_mock_process(
    responses: list[bytes],
) -> MagicMock:
    """Create a mock subprocess with stdout yielding *responses* then EOF."""
    stdout_iter = iter(responses)

    async def fake_readline() -> bytes:
        try:
            return next(stdout_iter)
        except StopIteration:
            return b""

    mock_process = MagicMock()
    mock_process.stdin = MagicMock()
    mock_process.stdin.write = MagicMock()
    mock_process.stdin.drain = AsyncMock()
    mock_process.stdout = MagicMock()
    mock_process.stdout.readline = fake_readline
    mock_process.stderr = MagicMock()
    mock_process.stderr.readline = AsyncMock(return_value=b"")
    mock_process.returncode = None
    mock_process.terminate = MagicMock()
    mock_process.kill = MagicMock()
    mock_process.wait = AsyncMock()
    return mock_process


class TestMCPStdioClientCallTool:
    """Test call_tool and related methods using mocked subprocess."""

    @pytest.mark.asyncio
    async def test_call_tool_success(self) -> None:
        client = MCPStdioClient(command="echo", server_name="test")

        response_line = (
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [{"type": "text", "text": "hello world"}],
                    "isError": False,
                },
            })
            + "\n"
        ).encode()

        client._process = _make_mock_process([response_line])
        client._reader_task = asyncio.create_task(client._read_responses())
        client._stderr_task = asyncio.create_task(client._drain_stderr())

        result = await client.call_tool("my_tool", {"arg": "val"})

        assert not result.is_error
        assert result.content == "hello world"

        await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_mcp_error(self) -> None:
        client = MCPStdioClient(command="echo", server_name="test")

        response_line = (
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "content": [{"type": "text", "text": "something went wrong"}],
                    "isError": True,
                },
            })
            + "\n"
        ).encode()

        client._process = _make_mock_process([response_line])
        client._reader_task = asyncio.create_task(client._read_responses())
        client._stderr_task = asyncio.create_task(client._drain_stderr())

        result = await client.call_tool("my_tool", {})

        assert result.is_error
        assert "something went wrong" in result.content

        await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_timeout(self) -> None:
        client = MCPStdioClient(command="echo", server_name="test", timeout=0.1)

        # No responses at all — reader returns EOF immediately, future gets rejected
        client._process = _make_mock_process([])
        client._reader_task = asyncio.create_task(client._read_responses())
        client._stderr_task = asyncio.create_task(client._drain_stderr())

        # call_tool catches exceptions and returns MCPCallResult with is_error
        result = await client.call_tool("my_tool", {})
        assert result.is_error
        assert "failed" in result.content.lower()

        await client.close()


class TestMCPStdioClientReaderCrash:
    """Test that pending futures are rejected when the reader stops."""

    @pytest.mark.asyncio
    async def test_pending_futures_rejected_on_reader_exit(self) -> None:
        client = MCPStdioClient(command="echo", server_name="test", timeout=5.0)

        # Reader that immediately returns EOF (simulating process crash)
        async def eof_readline() -> bytes:
            return b""

        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdin.write = MagicMock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.readline = eof_readline
        mock_process.stderr = MagicMock()
        mock_process.stderr.readline = AsyncMock(return_value=b"")
        mock_process.returncode = None
        mock_process.terminate = MagicMock()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()

        client._process = mock_process

        # Manually add a pending future
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        client._pending[99] = future

        # Start reader — it will exit immediately and reject pending
        reader_task = asyncio.create_task(client._read_responses())
        await reader_task

        assert future.done()
        with pytest.raises(RuntimeError, match="reader stopped"):
            future.result()

        await client.close()


# ---------------------------------------------------------------------------
# Protocol version constant
# ---------------------------------------------------------------------------


class TestProtocolVersion:
    def test_protocol_version_is_string(self) -> None:
        assert isinstance(MCP_PROTOCOL_VERSION, str)
        assert len(MCP_PROTOCOL_VERSION) > 0


# ---------------------------------------------------------------------------
# Registry merge
# ---------------------------------------------------------------------------


class TestRegistryMerge:
    def test_merge_two_registries(self) -> None:
        from agent.tools.sandbox.database import DbCreate, DbQuery

        r1 = ToolRegistry().register(DbCreate())
        r2 = ToolRegistry().register(DbQuery())
        merged = r1.merge(r2)
        assert merged.get("database_create") is not None
        assert merged.get("database_query") is not None

    def test_merge_collision_raises(self) -> None:
        from agent.tools.sandbox.database import DbCreate

        r1 = ToolRegistry().register(DbCreate())
        r2 = ToolRegistry().register(DbCreate())
        with pytest.raises(ValueError):
            r1.merge(r2)

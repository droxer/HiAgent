"""MCP (Model Context Protocol) server management route handlers."""

from __future__ import annotations

import json
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path
from loguru import logger

from agent.mcp.bridge import MCPBridgedTool
from agent.mcp.client import MCPStdioClient
from agent.mcp.config import MCPServerConfig
from agent.tools.registry import ToolRegistry
from api.dependencies import AppState, get_app_state
from api.models import MCPServerCreateRequest, MCPServerResponse
from api.auth import common_dependencies
from config.settings import get_settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MCP_BLOCKED_ENV_VARS = {
    "PATH", "LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH",
    "NODE_PATH", "HOME", "USER",
}

_ALLOWED_MCP_COMMANDS = {"npx", "uvx", "node", "python", "python3"}

router = APIRouter(prefix="/mcp", dependencies=common_dependencies)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _parse_mcp_configs(raw: str) -> tuple[MCPServerConfig, ...]:
    """Parse MCP_SERVERS JSON string into validated config objects."""
    entries = json.loads(raw)
    configs: list[MCPServerConfig] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        try:
            configs.append(
                MCPServerConfig(
                    name=entry.get("name", "unknown"),
                    transport=entry.get("transport", "stdio"),
                    command=entry.get("command", ""),
                    args=tuple(entry.get("args", [])),
                    url=entry.get("url", ""),
                    env=tuple((k, v) for k, v in entry.get("env", {}).items()),
                    timeout=float(entry.get("timeout", 30.0)),
                )
            )
        except (ValueError, TypeError) as exc:
            logger.warning(
                "mcp_config_invalid name={} error={}", entry.get("name"), exc
            )
    return tuple(configs)


async def _discover_mcp_tools(
    mcp_state: Any,
    registry: ToolRegistry,
) -> tuple[ToolRegistry, dict[str, MCPStdioClient], dict[str, MCPServerConfig]]:
    """Connect to configured MCP servers and register their tools.

    Returns the updated registry, a dict of active MCP clients keyed by
    server name, and a dict of their configs (for cleanup and introspection).
    """
    settings = get_settings()
    if not settings.MCP_SERVERS:
        return registry, {}, {}

    try:
        server_configs = _parse_mcp_configs(settings.MCP_SERVERS)
    except json.JSONDecodeError:
        logger.warning("Invalid MCP_SERVERS JSON, skipping MCP discovery")
        return registry, {}, {}

    clients: dict[str, MCPStdioClient] = {}
    configs: dict[str, MCPServerConfig] = {}
    for cfg in server_configs:
        if cfg.transport != "stdio":
            logger.warning(
                "Only stdio MCP transport supported, skipping {}", cfg.name
            )
            continue

        client = MCPStdioClient(
            command=cfg.command,
            args=cfg.args,
            env=cfg.env,
            server_name=cfg.name,
            timeout=cfg.timeout,
        )
        try:
            await client.connect()
            tools = await client.list_tools()
            for schema in tools:
                bridged = MCPBridgedTool(schema, client)
                try:
                    registry = registry.register(bridged)
                    logger.info(
                        "mcp_tool_registered name={} server={}",
                        schema.name,
                        schema.server_name,
                    )
                except ValueError:
                    logger.warning(
                        "mcp_tool_skipped name={} (already registered)", schema.name
                    )
            clients[cfg.name] = client
            configs[cfg.name] = cfg
        except Exception as exc:
            logger.error(
                "mcp_server_connect_failed name={} error={}", cfg.name, exc
            )
            await client.close()

    return registry, clients, configs


def _client_is_alive(client: MCPStdioClient) -> bool:
    """Return True if the MCP client's subprocess is still running."""
    proc = getattr(client, "_process", None)
    if proc is None:
        return False
    return proc.returncode is None


def _build_server_response(mcp_state: Any, name: str) -> MCPServerResponse:
    """Build a response model for a single MCP server."""
    cfg = mcp_state.configs.get(name)
    client = mcp_state.clients.get(name)

    tool_count = 0
    if mcp_state.registry is not None:
        for defn in mcp_state.registry.list_tools():
            if name in (defn.tags or ()):
                tool_count += 1

    return MCPServerResponse(
        name=name,
        transport=cfg.transport if cfg else "stdio",
        command=cfg.command if cfg else "",
        url=cfg.url if cfg else "",
        status="connected" if client and _client_is_alive(client) else "disconnected",
        tool_count=tool_count,
    )


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.get("/servers")
async def list_servers(
    state: AppState = Depends(get_app_state),
) -> dict:
    """GET /mcp/servers - list all configured MCP servers."""
    mcp_state = state.mcp_state
    servers = [_build_server_response(mcp_state, name) for name in mcp_state.configs]
    return {"servers": [s.model_dump() for s in servers]}


@router.post("/servers", status_code=201)
async def add_server(
    request: MCPServerCreateRequest,
    state: AppState = Depends(get_app_state),
) -> MCPServerResponse:
    """POST /mcp/servers - add and connect a new MCP server."""
    mcp_state = state.mcp_state

    if request.name in mcp_state.configs:
        raise HTTPException(status_code=409, detail=f"Server '{request.name}' already exists")

    if request.transport != "stdio":
        raise HTTPException(status_code=400, detail="Only stdio transport is currently supported")

    # Validate the command against the allowlist
    command_basename = os.path.basename(request.command)
    if command_basename not in _ALLOWED_MCP_COMMANDS:
        raise HTTPException(
            status_code=403,
            detail=f"Command '{command_basename}' is not in the allowed MCP commands: {sorted(_ALLOWED_MCP_COMMANDS)}",
        )

    # Filter blocked environment variables
    sanitized_env = {
        k: v for k, v in request.env.items() if k not in _MCP_BLOCKED_ENV_VARS
    }

    cfg = MCPServerConfig(
        name=request.name,
        transport=request.transport,
        command=request.command,
        args=tuple(request.args),
        url=request.url,
        env=tuple(sanitized_env.items()),
        timeout=request.timeout,
    )

    client = MCPStdioClient(
        command=cfg.command,
        args=cfg.args,
        env=cfg.env,
        server_name=cfg.name,
        timeout=cfg.timeout,
    )

    async with mcp_state.lock:
        try:
            await client.connect()
            tools = await client.list_tools()
            registry = mcp_state.registry or ToolRegistry()
            for schema in tools:
                bridged = MCPBridgedTool(schema, client)
                try:
                    registry = registry.register(bridged)
                except ValueError:
                    logger.warning("mcp_tool_skipped name={} (already registered)", schema.name)
            mcp_state.registry = registry
            mcp_state.clients[cfg.name] = client
            mcp_state.configs[cfg.name] = cfg
        except Exception as exc:
            await client.close()
            raise HTTPException(status_code=502, detail=f"Failed to connect: {exc}") from exc

    return _build_server_response(mcp_state, cfg.name)


@router.delete("/servers/{name}")
async def remove_server(
    name: str = Path(...),
    state: AppState = Depends(get_app_state),
) -> dict:
    """DELETE /mcp/servers/{name} - disconnect and remove an MCP server."""
    mcp_state = state.mcp_state

    if name not in mcp_state.configs:
        raise HTTPException(status_code=404, detail=f"Server '{name}' not found")

    async with mcp_state.lock:
        client = mcp_state.clients.pop(name, None)
        if client is not None:
            await client.close()

        mcp_state.configs.pop(name, None)

        if mcp_state.registry is not None:
            mcp_state.registry = mcp_state.registry.remove_by_tag(name)

    return {"detail": f"Server '{name}' removed"}

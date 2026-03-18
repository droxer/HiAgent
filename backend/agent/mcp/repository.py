"""Data access for persisted MCP server configurations."""

from __future__ import annotations

import json

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.mcp.config import MCPServerConfig
from agent.mcp.models import MCPServerModel


async def list_mcp_servers(session: AsyncSession) -> tuple[MCPServerConfig, ...]:
    """Load all persisted MCP server configs."""
    result = await session.execute(
        select(MCPServerModel).order_by(MCPServerModel.created_at)
    )
    rows = result.scalars().all()
    return tuple(_to_config(row) for row in rows)


async def save_mcp_server(session: AsyncSession, config: MCPServerConfig) -> None:
    """Persist an MCP server config (insert or update by name)."""
    result = await session.execute(
        select(MCPServerModel).where(MCPServerModel.name == config.name)
    )
    existing = result.scalar_one_or_none()

    if existing is not None:
        existing.transport = config.transport
        existing.command = config.command
        existing.args = json.dumps(list(config.args))
        existing.url = config.url
        existing.env = json.dumps(dict(config.env))
        existing.timeout = config.timeout
    else:
        session.add(
            MCPServerModel(
                name=config.name,
                transport=config.transport,
                command=config.command,
                args=json.dumps(list(config.args)),
                url=config.url,
                env=json.dumps(dict(config.env)),
                timeout=config.timeout,
            )
        )
    await session.commit()


async def delete_mcp_server(session: AsyncSession, name: str) -> bool:
    """Delete a persisted MCP server config by name. Returns True if deleted."""
    result = await session.execute(
        delete(MCPServerModel).where(MCPServerModel.name == name)
    )
    await session.commit()
    return result.rowcount > 0


def _to_config(model: MCPServerModel) -> MCPServerConfig:
    """Convert an ORM model to a frozen MCPServerConfig."""
    args = json.loads(model.args) if model.args else []
    env_dict = json.loads(model.env) if model.env else {}
    return MCPServerConfig(
        name=model.name,
        transport=model.transport,
        command=model.command or "",
        args=tuple(args),
        url=model.url or "",
        env=tuple(env_dict.items()),
        timeout=model.timeout or 30.0,
    )

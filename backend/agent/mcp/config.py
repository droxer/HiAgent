"""MCP server configuration."""

from __future__ import annotations

from dataclasses import dataclass


_VALID_TRANSPORTS = frozenset({"stdio", "sse"})


@dataclass(frozen=True)
class MCPServerConfig:
    """Immutable configuration for an MCP server connection.

    Attributes:
        name: Human-readable server name.
        transport: Connection method ("stdio" or "sse").
        command: For stdio transport, the command to spawn the server.
        args: For stdio transport, command arguments.
        url: For SSE transport, the server URL.
        env: Environment variables to pass to stdio server.
        timeout: Per-server request timeout in seconds.
    """

    name: str
    transport: str  # "stdio" or "sse"
    command: str = ""
    args: tuple[str, ...] = ()
    url: str = ""
    env: tuple[tuple[str, str], ...] = ()
    timeout: float = 30.0
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.transport not in _VALID_TRANSPORTS:
            raise ValueError(
                f"Unsupported MCP transport {self.transport!r}; "
                f"expected one of {sorted(_VALID_TRANSPORTS)}"
            )
        if self.transport == "stdio" and not self.command:
            raise ValueError("stdio transport requires a command")
        if self.transport == "sse" and not self.url:
            raise ValueError("sse transport requires a url")

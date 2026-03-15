"""Tool executor that routes calls based on execution context."""

from __future__ import annotations

from typing import Any

from loguru import logger

from agent.tools.base import LocalTool, SandboxTool, ToolResult
from agent.tools.registry import ToolRegistry


class ToolExecutor:
    """Routes tool calls to the appropriate execution environment.

    Sandbox sessions are created lazily on first sandbox tool call.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        sandbox_provider: Any | None = None,
        sandbox_config: Any | None = None,
        event_emitter: Any | None = None,
    ) -> None:
        self._registry = registry
        self._sandbox_provider = sandbox_provider
        self._sandbox_config = sandbox_config
        self._sandbox_session: Any | None = None
        self._event_emitter = event_emitter

    async def _get_sandbox_session(self) -> Any:
        """Lazily create a sandbox session on first use."""
        if self._sandbox_session is not None:
            return self._sandbox_session

        if self._sandbox_provider is None:
            raise RuntimeError(
                "No sandbox provider configured. "
                "Set a SandboxProvider to use sandbox tools."
            )

        from agent.sandbox.base import SandboxConfig

        config = self._sandbox_config or SandboxConfig(template="default")
        self._sandbox_session = await self._sandbox_provider.create_session(config)
        logger.info("Sandbox session created (template=%s)", config.template)
        return self._sandbox_session

    async def execute(
        self,
        tool_name: str,
        tool_input: dict,
    ) -> ToolResult:
        """Execute a tool by name with the given input.

        Local tools are called directly.
        Sandbox tools are routed through a lazily-created sandbox session.
        """
        tool = self._registry.get(tool_name)

        if tool is None:
            return ToolResult.fail(f"Unknown tool: {tool_name}")

        try:
            if isinstance(tool, LocalTool):
                return await tool.execute(**tool_input)

            if isinstance(tool, SandboxTool):
                session = await self._get_sandbox_session()
                return await tool.execute(
                    session=session,
                    event_emitter=self._event_emitter,
                    **tool_input,
                )

            return ToolResult.fail(
                f"Tool '{tool_name}' has an unrecognised type: {type(tool).__name__}",
            )
        except Exception as exc:
            return ToolResult.fail(f"Tool '{tool_name}' failed: {exc}")

    async def cleanup(self) -> None:
        """Clean up sandbox resources.

        Safe to call multiple times; a second call is a no-op.
        Handles the case where the session or provider is ``None``.
        """
        session = self._sandbox_session
        if session is None:
            return

        # Clear reference first to prevent double-cleanup even if
        # destroy_session raises.
        self._sandbox_session = None

        if self._sandbox_provider is None:
            logger.warning("Sandbox session exists but no provider to destroy it")
            return

        try:
            await self._sandbox_provider.destroy_session(session)
            logger.info("Sandbox session destroyed")
        except Exception as exc:
            logger.error("Failed to destroy sandbox session: %s", exc)

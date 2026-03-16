"""Tool executor that routes calls based on execution context."""

from __future__ import annotations

from typing import Any

from loguru import logger

from agent.artifacts.manager import ArtifactManager
from agent.tools.base import LocalTool, SandboxTool, ToolResult
from agent.tools.registry import ToolRegistry
from api.events import EventType


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
        artifact_manager: ArtifactManager | None = None,
    ) -> None:
        self._registry = registry
        self._sandbox_provider = sandbox_provider
        self._sandbox_config = sandbox_config
        self._sandbox_session: Any | None = None
        self._event_emitter = event_emitter
        self._artifact_manager = artifact_manager or ArtifactManager()

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

    @property
    def artifact_manager(self) -> ArtifactManager:
        """Expose the artifact manager for API endpoint access."""
        return self._artifact_manager

    async def execute(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> ToolResult:
        """Execute a tool by name with the given input.

        Local tools are called directly.
        Sandbox tools are routed through a lazily-created sandbox session.
        After sandbox tool execution, any file artifacts referenced in
        the result metadata are extracted and ARTIFACT_CREATED events emitted.
        """
        tool = self._registry.get(tool_name)

        if tool is None:
            return ToolResult.fail(f"Unknown tool: {tool_name}")

        try:
            if isinstance(tool, LocalTool):
                return await tool.execute(**tool_input)

            if isinstance(tool, SandboxTool):
                session = await self._get_sandbox_session()
                logger.debug(
                    "sandbox_tool_input name={} keys={}",
                    tool_name,
                    list(tool_input.keys()),
                )
                result = await tool.execute(
                    session=session,
                    event_emitter=self._event_emitter,
                    **tool_input,
                )
                result = await self._extract_artifacts(result, session)
                return result

            return ToolResult.fail(
                f"Tool '{tool_name}' has an unrecognised type: {type(tool).__name__}",
            )
        except Exception as exc:
            return ToolResult.fail(f"Tool '{tool_name}' failed: {exc}")

    async def _extract_artifacts(
        self,
        result: ToolResult,
        session: Any,
    ) -> ToolResult:
        """Extract file artifacts from a sandbox tool result.

        Looks for ``artifact_paths`` in the result metadata. If present,
        downloads the files via ArtifactManager and emits ARTIFACT_CREATED
        events for each. Returns a new ToolResult with ``artifact_ids``
        added to metadata so the frontend can associate files with tool calls.
        """
        if not result.success or result.metadata is None:
            return result

        artifact_paths = result.metadata.get("artifact_paths")
        if not artifact_paths:
            return result

        path_list = list(artifact_paths)
        artifacts = await self._artifact_manager.extract_from_sandbox(
            session=session,
            remote_paths=path_list,
        )

        if len(artifacts) < len(path_list):
            logger.warning(
                "Only %d of %d artifact paths were extracted",
                len(artifacts),
                len(path_list),
            )

        artifact_ids: list[str] = []
        if self._event_emitter is not None:
            for artifact in artifacts:
                artifact_ids.append(artifact.id)
                await self._event_emitter.emit(
                    EventType.ARTIFACT_CREATED,
                    {
                        "artifact_id": artifact.id,
                        "storage_key": artifact.path,
                        "name": artifact.original_name,
                        "content_type": artifact.content_type,
                        "size": artifact.size,
                    },
                )

        # Return a new result with artifact_ids in metadata
        if artifact_ids:
            updated_meta = dict(result.metadata)
            updated_meta["artifact_ids"] = artifact_ids
            return ToolResult.ok(result.output, metadata=updated_meta)

        return result

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

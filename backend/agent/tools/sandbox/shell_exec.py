"""Shell command execution inside a sandbox."""

from __future__ import annotations

import asyncio
from typing import Any

from agent.sandbox.base import ExtendedSandboxSession
from agent.tools.base import (
    ExecutionContext,
    SandboxTool,
    ToolDefinition,
    ToolResult,
)


def _make_stream_callbacks(
    event_emitter: Any,
) -> tuple[Any, Any]:
    """Create thread-safe stdout/stderr callbacks that emit SSE events."""
    from api.events import EventType

    loop = asyncio.get_running_loop()

    def on_stdout(line: str) -> None:
        asyncio.run_coroutine_threadsafe(
            event_emitter.emit(EventType.SANDBOX_STDOUT, {"text": line}),
            loop,
        )

    def on_stderr(line: str) -> None:
        asyncio.run_coroutine_threadsafe(
            event_emitter.emit(EventType.SANDBOX_STDERR, {"text": line}),
            loop,
        )

    return on_stdout, on_stderr


class ShellExec(SandboxTool):
    """Execute a shell command inside the sandbox."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="shell_exec",
            description="Execute a shell command inside the sandbox environment.",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds.",
                        "default": 30,
                    },
                    "workdir": {
                        "type": "string",
                        "description": "Working directory for the command.",
                    },
                },
                "required": ["command"],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("shell", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        command: str = kwargs.get("command", "")
        timeout: int = kwargs.get("timeout", 30)
        workdir: str | None = kwargs.get("workdir")
        event_emitter: Any | None = kwargs.get("event_emitter")

        if not command.strip():
            return ToolResult.fail("Command must not be empty")

        try:
            use_streaming = (
                event_emitter is not None
                and isinstance(session, ExtendedSandboxSession)
            )

            if use_streaming:
                on_stdout, on_stderr = _make_stream_callbacks(event_emitter)
                result = await session.exec_stream(
                    command,
                    on_stdout=on_stdout,
                    on_stderr=on_stderr,
                    timeout=timeout,
                    workdir=workdir,
                )
            else:
                result = await session.exec(
                    command, timeout=timeout, workdir=workdir
                )
        except Exception as exc:
            return ToolResult.fail(f"Shell execution failed: {exc}")

        combined = result.stdout
        if result.stderr:
            combined = (
                f"{combined}\n[stderr]\n{result.stderr}" if combined else result.stderr
            )

        return ToolResult.ok(
            combined,
            metadata={"exit_code": result.exit_code},
        )

"""Run code snippets inside a sandbox."""

from __future__ import annotations

import shlex
from typing import Any

from agent.sandbox.base import ExtendedSandboxSession
from agent.tools.base import (
    ExecutionContext,
    SandboxTool,
    ToolDefinition,
    ToolResult,
)

_RUNTIME_MAP: dict[str, str] = {
    "python": "python3",
    "javascript": "node",
    "js": "node",
    "node": "node",
    "bash": "bash",
    "sh": "sh",
}

_EXTENSION_MAP: dict[str, str] = {
    "python": ".py",
    "javascript": ".js",
    "js": ".js",
    "node": ".js",
    "bash": ".sh",
    "sh": ".sh",
}


class CodeRun(SandboxTool):
    """Write code to a temp file and execute it inside the sandbox."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="code_run",
            description=(
                "Write a code snippet to a temporary file and execute it "
                "inside the sandbox with the appropriate runtime."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The source code to execute.",
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (python, javascript, bash).",
                        "default": "python",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename for the script.",
                    },
                },
                "required": ["code"],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("code", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        code: str = kwargs.get("code", "")
        language: str = kwargs.get("language", "python").lower()
        filename: str | None = kwargs.get("filename")
        event_emitter: Any | None = kwargs.get("event_emitter")

        if not code.strip():
            return ToolResult.fail("Code must not be empty")

        runtime = _RUNTIME_MAP.get(language)
        if runtime is None:
            supported = ", ".join(sorted(_RUNTIME_MAP.keys()))
            return ToolResult.fail(
                f"Unsupported language '{language}'. Supported: {supported}"
            )

        extension = _EXTENSION_MAP[language]
        target = filename or f"/tmp/_code_run{extension}"

        try:
            await session.write_file(target, code)
        except Exception as exc:
            return ToolResult.fail(f"Failed to write code file: {exc}")

        try:
            command = f"{runtime} {shlex.quote(target)}"
            use_streaming = (
                event_emitter is not None
                and isinstance(session, ExtendedSandboxSession)
            )

            if use_streaming:
                from agent.tools.sandbox.shell_exec import _make_stream_callbacks

                on_stdout, on_stderr = _make_stream_callbacks(event_emitter)
                result = await session.exec_stream(
                    command,
                    on_stdout=on_stdout,
                    on_stderr=on_stderr,
                    timeout=30,
                )
            else:
                result = await session.exec(command, timeout=30)
        except Exception as exc:
            return ToolResult.fail(f"Code execution failed: {exc}")

        combined = result.stdout
        if result.stderr:
            combined = (
                f"{combined}\n[stderr]\n{result.stderr}" if combined else result.stderr
            )

        return ToolResult.ok(
            combined,
            metadata={"exit_code": result.exit_code, "language": language},
        )

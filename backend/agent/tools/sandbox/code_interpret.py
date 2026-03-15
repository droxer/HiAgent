"""Code interpreter tool with rich output support."""

from __future__ import annotations

from typing import Any

from agent.sandbox.base import ExtendedSandboxSession
from agent.tools.base import (
    ExecutionContext,
    SandboxTool,
    ToolDefinition,
    ToolResult,
)


class CodeInterpret(SandboxTool):
    """Execute code with rich output support (charts, DataFrames, images)."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="code_interpret",
            description=(
                "Execute code using the sandbox code interpreter. "
                "Supports rich output including charts, DataFrames, "
                "and images. Preferred for data analysis tasks."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The code to execute.",
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (default: python).",
                        "default": "python",
                    },
                },
                "required": ["code"],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("code", "sandbox", "interpreter"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        code: str = kwargs.get("code", "")
        language: str = kwargs.get("language", "python").lower()

        if not code.strip():
            return ToolResult.fail("Code must not be empty")

        if not isinstance(session, ExtendedSandboxSession):
            return ToolResult.fail(
                "Code interpreter not supported by this sandbox provider"
            )

        try:
            result = await session.run_code(code, language=language)
        except Exception as exc:
            return ToolResult.fail(f"Code interpreter failed: {exc}")

        parts: list[str] = []
        if result.stdout:
            parts.append(result.stdout)
        if result.stderr:
            parts.append(f"[stderr]\n{result.stderr}")
        if result.error:
            parts.append(f"[error]\n{result.error}")

        rich_outputs: list[dict[str, str]] = [
            {
                "mime_type": o.mime_type,
                "data": o.data,
                "display_type": o.display_type,
            }
            for o in result.results
        ]

        output_text = "\n".join(parts) if parts else "(no output)"

        return ToolResult.ok(
            output_text,
            metadata={
                "language": language,
                "has_error": result.error is not None,
                "rich_outputs": rich_outputs,
            },
        )

"""Document reading tool for the sandbox."""

from __future__ import annotations

from typing import Any

from agent.tools.base import (
    ExecutionContext,
    SandboxTool,
    ToolDefinition,
    ToolResult,
)

_TEXT_EXTENSIONS = frozenset({".txt", ".md", ".json", ".log", ".yaml", ".yml", ".xml"})
_DOC_SCRIPT_PATH = "/tmp/_doc_read_script.py"


def _get_extension(path: str) -> str:
    """Extract the lowercase file extension from a path."""
    dot_idx = path.rfind(".")
    if dot_idx == -1:
        return ""
    return path[dot_idx:].lower()


class DocRead(SandboxTool):
    """Read and extract content from documents inside the sandbox."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="document_read",
            description=(
                "Read a document file inside the sandbox. Supports PDF, CSV, "
                "and plain text formats (.txt, .md, .json, .log, .yaml, .xml)."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the document file.",
                    },
                },
                "required": ["path"],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("document", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        path: str = kwargs.get("path", "")
        if not path.strip():
            return ToolResult.fail("Path must not be empty")

        ext = _get_extension(path)

        if ext == ".csv":
            return await self._read_csv(session, path)
        if ext == ".pdf":
            return await self._read_pdf(session, path)
        if ext in _TEXT_EXTENSIONS or ext == "":
            return await self._read_text(session, path)

        return ToolResult.fail(f"Unsupported file extension: '{ext}'")

    async def _read_text(self, session: Any, path: str) -> ToolResult:
        try:
            content = await session.read_file(path)
        except Exception as exc:
            return ToolResult.fail(f"Failed to read file: {exc}")

        return ToolResult.ok(content, metadata={"path": path, "format": "text"})

    async def _read_csv(self, session: Any, path: str) -> ToolResult:
        script = (
            "import csv\n"
            f"f = open({path!r}, newline='')\n"
            "reader = csv.reader(f)\n"
            "rows = list(reader)\n"
            "f.close()\n"
            "print(f'Rows: {len(rows)}')\n"
            "for r in rows[:50]: print('|'.join(r))\n"
        )
        try:
            await session.write_file(_DOC_SCRIPT_PATH, script)
            result = await session.exec(f"python3 {_DOC_SCRIPT_PATH}", timeout=15)
        except Exception as exc:
            return ToolResult.fail(f"Failed to read CSV: {exc}")

        if not result.success:
            return ToolResult.fail(
                f"CSV read failed (exit {result.exit_code}): {result.stderr}"
            )

        return ToolResult.ok(result.stdout, metadata={"path": path, "format": "csv"})

    async def _read_pdf(self, session: Any, path: str) -> ToolResult:
        script = (
            "import subprocess\n"
            f"r = subprocess.run(['pdftotext', {path!r}, '-'],\n"
            "    capture_output=True, text=True)\n"
            "print(r.stdout[:10000] if r.returncode == 0 else\n"
            "      f'pdftotext failed: {r.stderr}')\n"
        )
        try:
            await session.write_file(_DOC_SCRIPT_PATH, script)
            result = await session.exec(f"python3 {_DOC_SCRIPT_PATH}", timeout=30)
        except Exception as exc:
            return ToolResult.fail(f"Failed to read PDF: {exc}")

        if not result.success:
            return ToolResult.fail(
                f"PDF read failed (exit {result.exit_code}): {result.stderr}"
            )

        return ToolResult.ok(result.stdout, metadata={"path": path, "format": "pdf"})

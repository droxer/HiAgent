"""Fetch and extract text content from a URL."""

from __future__ import annotations

import re
from typing import Any

import httpx

from agent.tools.base import (
    ExecutionContext,
    LocalTool,
    ToolDefinition,
    ToolResult,
)

_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\n{3,}")


def _strip_html(html: str) -> str:
    """Remove script/style blocks, then strip remaining HTML tags."""
    text = _SCRIPT_STYLE_RE.sub("", html)
    text = _HTML_TAG_RE.sub("", text)
    text = _WHITESPACE_RE.sub("\n\n", text)
    return text.strip()


class WebFetch(LocalTool):
    """Fetch a web page and return its text content."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="web_fetch",
            description="Fetch a URL and return its text content with HTML stripped.",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch.",
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum character length of returned content.",
                        "default": 20000,
                    },
                },
                "required": ["url"],
            },
            execution_context=ExecutionContext.LOCAL,
            tags=("web", "fetch"),
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        url: str = kwargs.get("url", "")
        max_length: int = kwargs.get("max_length", 20000)

        if not url.strip():
            return ToolResult.fail("URL must not be empty")

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return ToolResult.fail(f"HTTP {exc.response.status_code}: {exc}")
        except Exception as exc:
            return ToolResult.fail(f"Fetch failed: {exc}")

        content = _strip_html(response.text)
        truncated = len(content) > max_length
        content = content[:max_length]

        return ToolResult.ok(
            content,
            metadata={"url": url, "truncated": truncated, "length": len(content)},
        )

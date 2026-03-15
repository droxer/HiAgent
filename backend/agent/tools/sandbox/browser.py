"""Browser automation tools using Playwright inside a sandbox."""

from __future__ import annotations

from typing import Any

from agent.tools.base import (
    ExecutionContext,
    SandboxTool,
    ToolDefinition,
    ToolResult,
)

_SCREENSHOT_PATH = "/tmp/screenshot.png"
_SCRIPT_PATH = "/tmp/browser_action.py"
_WS_FILE = "/tmp/browser_ws.txt"

_VALID_DIRECTIONS = frozenset({"up", "down"})
_VALID_EXTRACT_TYPES = frozenset({"text", "links", "tables"})


def _build_browser_script(action_code: str) -> str:
    """Wrap action code with Playwright browser setup and screenshot."""
    return f'''\
from playwright.sync_api import sync_playwright
import os

WS_FILE = "{_WS_FILE}"


def get_browser():
    p = sync_playwright().start()
    if os.path.exists(WS_FILE):
        try:
            ws = open(WS_FILE).read().strip()
            browser = p.chromium.connect(ws)
            return p, browser
        except Exception:
            pass
    browser = p.chromium.launch(headless=True)
    return p, browser


p, browser = get_browser()
if browser.contexts:
    page = browser.contexts[0].pages[0]
else:
    page = browser.new_context().new_page()

{action_code}

page.screenshot(path="{_SCREENSHOT_PATH}")
'''


async def _run_browser_script(session: Any, script: str) -> tuple[str, int]:
    """Write and execute a browser script, returning stdout and exit code."""
    await session.write_file(_SCRIPT_PATH, script)
    result = await session.exec(f"python3 {_SCRIPT_PATH}", timeout=60)
    output = result.stdout or ""
    if result.stderr:
        output = f"{output}\n[stderr]\n{result.stderr}" if output else result.stderr
    return output, result.exit_code


class BrowserNavigate(SandboxTool):
    """Navigate to a URL and take a screenshot."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="browser_navigate",
            description="Navigate the browser to a URL, take a screenshot, and return the page title.",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to.",
                    },
                },
                "required": ["url"],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("browser", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        url: str = kwargs.get("url", "")
        if not url.strip():
            return ToolResult.fail("URL must not be empty")

        escaped_url = url.replace('"', '\\"')
        action_code = (
            f'page.goto("{escaped_url}", wait_until="domcontentloaded")\n'
            f"print(page.title())"
        )
        script = _build_browser_script(action_code)

        try:
            output, exit_code = await _run_browser_script(session, script)
        except Exception as exc:
            return ToolResult.fail(f"Browser navigation failed: {exc}")

        if exit_code != 0:
            return ToolResult.fail(f"Navigation error (exit {exit_code}): {output}")

        title = output.strip().split("\n")[0] if output.strip() else "Unknown"
        return ToolResult.ok(
            f"Navigated to {url}. Page title: {title}",
            metadata={"screenshot": _SCREENSHOT_PATH, "title": title},
        )


class BrowserClick(SandboxTool):
    """Click an element by CSS selector and take a screenshot."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="browser_click",
            description="Click an element matching a CSS selector and take a screenshot.",
            input_schema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the element to click.",
                    },
                },
                "required": ["selector"],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("browser", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        selector: str = kwargs.get("selector", "")
        if not selector.strip():
            return ToolResult.fail("Selector must not be empty")

        escaped = selector.replace('"', '\\"')
        action_code = f'page.click("{escaped}")\npage.wait_for_timeout(500)'
        script = _build_browser_script(action_code)

        try:
            output, exit_code = await _run_browser_script(session, script)
        except Exception as exc:
            return ToolResult.fail(f"Browser click failed: {exc}")

        if exit_code != 0:
            return ToolResult.fail(f"Click error (exit {exit_code}): {output}")

        return ToolResult.ok(
            f"Clicked element: {selector}",
            metadata={"screenshot": _SCREENSHOT_PATH, "selector": selector},
        )


class BrowserType(SandboxTool):
    """Type text into an input element by CSS selector."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="browser_type",
            description="Type text into an input element matching a CSS selector and take a screenshot.",
            input_schema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the input element.",
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type into the element.",
                    },
                },
                "required": ["selector", "text"],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("browser", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        selector: str = kwargs.get("selector", "")
        text: str = kwargs.get("text", "")

        if not selector.strip():
            return ToolResult.fail("Selector must not be empty")
        if not text:
            return ToolResult.fail("Text must not be empty")

        escaped_sel = selector.replace('"', '\\"')
        escaped_txt = text.replace('"', '\\"')
        action_code = (
            f'page.fill("{escaped_sel}", "{escaped_txt}")\npage.wait_for_timeout(300)'
        )
        script = _build_browser_script(action_code)

        try:
            output, exit_code = await _run_browser_script(session, script)
        except Exception as exc:
            return ToolResult.fail(f"Browser type failed: {exc}")

        if exit_code != 0:
            return ToolResult.fail(f"Type error (exit {exit_code}): {output}")

        return ToolResult.ok(
            f"Typed text into: {selector}",
            metadata={"screenshot": _SCREENSHOT_PATH, "selector": selector},
        )


class BrowserScroll(SandboxTool):
    """Scroll the page up or down by a given number of pixels."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="browser_scroll",
            description="Scroll the browser page up or down and take a screenshot.",
            input_schema={
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "Scroll direction: 'up' or 'down'.",
                        "enum": ["up", "down"],
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Number of pixels to scroll.",
                        "default": 500,
                    },
                },
                "required": ["direction"],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("browser", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        direction: str = kwargs.get("direction", "down").lower()
        amount: int = kwargs.get("amount", 500)

        if direction not in _VALID_DIRECTIONS:
            return ToolResult.fail(
                f"Invalid direction '{direction}'. Must be 'up' or 'down'."
            )
        if amount <= 0:
            return ToolResult.fail("Scroll amount must be a positive integer")

        pixels = -amount if direction == "up" else amount
        action_code = (
            f"page.evaluate('window.scrollBy(0, {pixels})')\npage.wait_for_timeout(300)"
        )
        script = _build_browser_script(action_code)

        try:
            output, exit_code = await _run_browser_script(session, script)
        except Exception as exc:
            return ToolResult.fail(f"Browser scroll failed: {exc}")

        if exit_code != 0:
            return ToolResult.fail(f"Scroll error (exit {exit_code}): {output}")

        return ToolResult.ok(
            f"Scrolled {direction} by {amount}px",
            metadata={"screenshot": _SCREENSHOT_PATH, "direction": direction},
        )


_EXTRACT_TEXT_CODE = """\
target = page.query_selector("{selector}")
el = target if target else page
print(el.inner_text())
"""

_EXTRACT_LINKS_CODE = """\
import json
target = page.query_selector("{selector}")
scope = target if target else page
links = scope.eval_on_selector_all(
    "a[href]",
    "els => els.map(e => ({{ text: e.innerText.trim(), href: e.href }}))"
)
for link in links:
    print(f"{{link['text']}} -> {{link['href']}}")
"""

_EXTRACT_TABLES_CODE = """\
import json
target = page.query_selector("{selector}")
scope = target if target else page
tables = scope.eval_on_selector_all(
    "table",
    \"\"\"els => els.map(table => {{
        const rows = Array.from(table.querySelectorAll("tr"));
        return rows.map(row => {{
            const cells = Array.from(row.querySelectorAll("th, td"));
            return cells.map(c => c.innerText.trim());
        }});
    }})\"\"\"
)
for i, table in enumerate(tables):
    print(f"--- Table {{i + 1}} ---")
    for row in table:
        print("\\t".join(row))
"""


def _build_extract_code(selector: str, extract_type: str) -> str:
    """Return the extraction action code for the given type."""
    escaped = selector.replace('"', '\\"') if selector else ""
    templates = {
        "text": _EXTRACT_TEXT_CODE,
        "links": _EXTRACT_LINKS_CODE,
        "tables": _EXTRACT_TABLES_CODE,
    }
    return templates[extract_type].format(selector=escaped)


class BrowserExtract(SandboxTool):
    """Extract content from the current page."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="browser_extract",
            description="Extract text, links, or tables from the current browser page.",
            input_schema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "Optional CSS selector to scope extraction.",
                    },
                    "extract_type": {
                        "type": "string",
                        "description": "What to extract: 'text', 'links', or 'tables'.",
                        "enum": ["text", "links", "tables"],
                        "default": "text",
                    },
                },
                "required": [],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("browser", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        selector: str = kwargs.get("selector", "")
        extract_type: str = kwargs.get("extract_type", "text").lower()

        if extract_type not in _VALID_EXTRACT_TYPES:
            return ToolResult.fail(
                f"Invalid extract_type '{extract_type}'. "
                f"Must be one of: {', '.join(sorted(_VALID_EXTRACT_TYPES))}"
            )

        action_code = _build_extract_code(selector, extract_type)
        script = _build_browser_script(action_code)

        try:
            output, exit_code = await _run_browser_script(session, script)
        except Exception as exc:
            return ToolResult.fail(f"Browser extraction failed: {exc}")

        if exit_code != 0:
            return ToolResult.fail(f"Extract error (exit {exit_code}): {output}")

        return ToolResult.ok(
            output.strip() if output.strip() else "(no content extracted)",
            metadata={
                "screenshot": _SCREENSHOT_PATH,
                "extract_type": extract_type,
            },
        )

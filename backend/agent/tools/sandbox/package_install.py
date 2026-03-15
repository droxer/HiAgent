"""Package installation tool for the sandbox."""

from __future__ import annotations

import re
from typing import Any

from agent.tools.base import (
    ExecutionContext,
    SandboxTool,
    ToolDefinition,
    ToolResult,
)

_MAX_PACKAGES = 10

_MANAGER_COMMANDS: dict[str, str] = {
    "pip": "pip install",
    "npm": "npm install",
}

_SAFE_PACKAGE_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+([=<>!~]+[a-zA-Z0-9_\-\.]+)?$")


def _validate_package_name(name: str) -> str | None:
    """Return an error message if the package name is unsafe, else None."""
    if not _SAFE_PACKAGE_RE.match(name):
        return f"Invalid package name: '{name}'"
    return None


class PackageInstall(SandboxTool):
    """Install packages inside the sandbox using pip or npm."""

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="package_install",
            description=(
                "Install one or more packages inside the sandbox. "
                "Supports pip and npm package managers."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "packages": {
                        "type": "string",
                        "description": "Space-separated list of package names.",
                    },
                    "manager": {
                        "type": "string",
                        "description": "Package manager to use (pip or npm).",
                        "default": "pip",
                        "enum": ["pip", "npm"],
                    },
                },
                "required": ["packages"],
            },
            execution_context=ExecutionContext.SANDBOX,
            tags=("package", "sandbox"),
        )

    async def execute(self, session: Any, **kwargs: Any) -> ToolResult:
        raw_packages: str = kwargs.get("packages", "")
        manager: str = kwargs.get("manager", "pip").lower()

        if not raw_packages.strip():
            return ToolResult.fail("Packages must not be empty")

        if manager not in _MANAGER_COMMANDS:
            supported = ", ".join(sorted(_MANAGER_COMMANDS.keys()))
            return ToolResult.fail(
                f"Unsupported manager '{manager}'. Supported: {supported}"
            )

        package_list = raw_packages.strip().split()

        if len(package_list) > _MAX_PACKAGES:
            return ToolResult.fail(
                f"Too many packages ({len(package_list)}). "
                f"Maximum {_MAX_PACKAGES} per call."
            )

        for pkg in package_list:
            error = _validate_package_name(pkg)
            if error is not None:
                return ToolResult.fail(error)

        command = f"{_MANAGER_COMMANDS[manager]} {' '.join(package_list)}"

        try:
            result = await session.exec(command, timeout=120)
        except Exception as exc:
            return ToolResult.fail(f"Package installation failed: {exc}")

        if not result.success:
            output = result.stderr or result.stdout
            return ToolResult.fail(
                f"Installation failed (exit {result.exit_code}): {output}"
            )

        return ToolResult.ok(
            result.stdout,
            metadata={
                "manager": manager,
                "packages": package_list,
                "exit_code": result.exit_code,
            },
        )

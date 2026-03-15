"""Tool registry for managing and querying available tools."""

from __future__ import annotations

from agent.tools.base import (
    ExecutionContext,
    LocalTool,
    SandboxTool,
    ToolDefinition,
)


class ToolRegistry:
    """Immutable-style registry of available tools.

    Each mutation method returns a new registry instance,
    leaving the original unchanged.
    """

    def __init__(
        self,
        tools: dict[str, LocalTool | SandboxTool] | None = None,
    ) -> None:
        self._tools: dict[str, LocalTool | SandboxTool] = dict(tools) if tools else {}

    # -- Mutation (returns new registry) ------------------------------------

    def register(self, tool: LocalTool | SandboxTool) -> ToolRegistry:
        """Return a new registry with *tool* added.

        Raises ValueError if a tool with the same name is already registered.
        """
        definition = tool.definition()
        name = definition.name

        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")

        new_tools = {**self._tools, name: tool}
        return ToolRegistry(tools=new_tools)

    # -- Queries ------------------------------------------------------------

    def get(self, name: str) -> LocalTool | SandboxTool | None:
        """Look up a tool by name, returning None if not found."""
        return self._tools.get(name)

    def list_tools(self) -> tuple[ToolDefinition, ...]:
        """Return definitions of all registered tools."""
        return tuple(tool.definition() for tool in self._tools.values())

    def is_sandbox_tool(self, name: str) -> bool:
        """Return True if *name* refers to a SandboxTool."""
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"Unknown tool: {name}")
        return isinstance(tool, SandboxTool)

    # -- Serialisation helpers ----------------------------------------------

    def to_anthropic_tools(self) -> list[dict]:
        """Convert all tools to Anthropic API format."""
        results: list[dict] = []
        for tool in self._tools.values():
            defn = tool.definition()
            results.append(
                {
                    "name": defn.name,
                    "description": defn.description,
                    "input_schema": defn.input_schema,
                }
            )
        return results

    def grouped_descriptions(self) -> str:
        """Return a human-readable string grouping tools by execution context."""
        groups: dict[ExecutionContext, list[ToolDefinition]] = {
            ExecutionContext.LOCAL: [],
            ExecutionContext.SANDBOX: [],
        }

        for tool in self._tools.values():
            defn = tool.definition()
            groups[defn.execution_context].append(defn)

        lines: list[str] = []
        for ctx, definitions in groups.items():
            if not definitions:
                continue
            lines.append(f"[{ctx.value.upper()}]")
            for defn in definitions:
                tags = f"  ({', '.join(defn.tags)})" if defn.tags else ""
                lines.append(f"  - {defn.name}: {defn.description}{tags}")
            lines.append("")

        return "\n".join(lines).rstrip()

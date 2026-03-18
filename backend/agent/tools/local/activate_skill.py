"""activate_skill tool — returns full SKILL.md instructions for LLM consumption."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from agent.skills.loader import SkillRegistry
from agent.tools.base import ExecutionContext, LocalTool, ToolDefinition, ToolResult

_MAX_FILES_PER_CATEGORY = 50


class ActivateSkill(LocalTool):
    """Tool that activates a skill by returning its full instructions."""

    def __init__(
        self,
        skill_registry: SkillRegistry,
        active_skill_name: str | None = None,
    ) -> None:
        self._registry = skill_registry
        self._active_skill_name = active_skill_name

    @property
    def active_skill_name(self) -> str | None:
        return self._active_skill_name

    # NOTE: No setter — active_skill_name is read-only.
    # To change the active skill, create a new ActivateSkill instance.

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="activate_skill",
            description=(
                "Activate a skill to receive expert methodology for a specific "
                "type of task. Skills are auto-activated when your request matches, "
                "but you can also manually activate for mid-conversation skill "
                "switches or explicit user requests."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the skill to activate.",
                    },
                },
                "required": ["name"],
            },
            execution_context=ExecutionContext.LOCAL,
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        name = kwargs.get("name", "")
        if not name:
            return ToolResult.fail("Missing required parameter: name")

        if name == self._active_skill_name:
            return ToolResult.ok(
                f'Skill "{name}" is already active (auto-activated for this turn).'
            )

        skill = self._registry.find_by_name(name)
        if skill is None:
            available = ", ".join(self._registry.names())
            return ToolResult.fail(
                f"Skill '{name}' not found. Available skills: {available}"
            )

        parts = [f'<skill_content name="{skill.metadata.name}">']
        parts.append(skill.instructions)
        parts.append("")
        parts.append(f"Skill directory: {skill.directory_path}")
        parts.append(
            "Resolve all relative paths in instructions against this directory."
        )

        resources = _categorize_resources(skill.directory_path)
        if any(resources.values()):
            parts.append("")
            parts.append("<skill_resources>")
            for category in ("scripts", "references", "assets"):
                files = resources.get(category, [])
                if files:
                    parts.append(f"  <{category}>")
                    for f in files[:_MAX_FILES_PER_CATEGORY]:
                        parts.append(f"    <file>{f}</file>")
                    if len(files) > _MAX_FILES_PER_CATEGORY:
                        parts.append(
                            f"    <!-- {len(files) - _MAX_FILES_PER_CATEGORY} more files -->"
                        )
                    parts.append(f"  </{category}>")
            other = resources.get("other", [])
            if other:
                parts.append("  <other>")
                for f in other[:_MAX_FILES_PER_CATEGORY]:
                    parts.append(f"    <file>{f}</file>")
                parts.append("  </other>")
            parts.append("</skill_resources>")

        parts.append("</skill_content>")

        return ToolResult.ok("\n".join(parts))


def _categorize_resources(directory: Path) -> dict[str, list[str]]:
    """Categorize non-SKILL.md files into scripts/references/assets/other."""
    categories: dict[str, list[str]] = {
        "scripts": [],
        "references": [],
        "assets": [],
        "other": [],
    }

    if not directory.is_dir():
        return categories

    for root, _dirs, files in os.walk(directory):
        for fname in sorted(files):
            if fname == "SKILL.md":
                continue
            rel = os.path.relpath(os.path.join(root, fname), directory)

            top_dir = rel.split(os.sep)[0] if os.sep in rel else None
            if top_dir in categories:
                categories[top_dir].append(rel)
            else:
                categories["other"].append(rel)

    return categories

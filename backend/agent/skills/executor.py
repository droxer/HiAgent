"""Skill execution engine."""

from __future__ import annotations

import copy
from typing import Any

from loguru import logger

from agent.skills.loader import SkillManifest
from agent.tools.base import ToolResult
from agent.tools.executor import ToolExecutor


class SkillExecutor:
    """Executes a skill's steps sequentially via a ToolExecutor."""

    def __init__(self, tool_executor: ToolExecutor) -> None:
        self._tool_executor = tool_executor

    async def execute_skill(
        self,
        skill: SkillManifest,
        variables: dict[str, Any],
    ) -> list[ToolResult]:
        """Execute all steps in a skill, resolving templates with variables.

        Stops on the first failure unless the failing step has a condition set.
        Returns the list of ToolResult objects produced by each executed step.
        """
        results: list[ToolResult] = []

        for step in skill.steps:
            if step.condition and not self._evaluate_condition(
                step.condition, variables
            ):
                logger.debug(
                    "Skipping step '%s' (condition not met: %s)",
                    step.description,
                    step.condition,
                )
                continue

            resolved_input = self._resolve_template(step.input_template, variables)

            logger.info(
                "Executing skill step: %s (tool=%s)",
                step.description,
                step.tool,
            )
            result = await self._tool_executor.execute(step.tool, resolved_input)
            results.append(result)

            if not result.success and step.condition is None:
                logger.warning(
                    "Skill '%s' aborted at step '%s': %s",
                    skill.name,
                    step.description,
                    result.error,
                )
                break

        return results

    @staticmethod
    def _resolve_template(
        template: dict[str, Any],
        variables: dict[str, Any],
    ) -> dict[str, Any]:
        """Deep-replace {placeholder} strings in template with variable values.

        Returns a new dict -- the original template is never mutated.
        """
        return _deep_resolve(template, variables)

    @staticmethod
    def _evaluate_condition(condition: str, variables: dict[str, Any]) -> bool:
        """Evaluate a simple condition string against variables.

        Supports basic presence checks like 'has_results' (truthy lookup).
        Returns False for any unrecognised or missing variable.
        """
        return bool(variables.get(condition, False))


def _deep_resolve(value: Any, variables: dict[str, Any]) -> Any:
    """Recursively resolve placeholders in a nested structure.

    Returns a new structure -- inputs are never mutated.
    """
    if isinstance(value, str):
        return _resolve_string(value, variables)

    if isinstance(value, dict):
        return {k: _deep_resolve(v, variables) for k, v in value.items()}

    if isinstance(value, list):
        return [_deep_resolve(item, variables) for item in value]

    # Scalars (int, float, bool, None) pass through unchanged.
    return copy.deepcopy(value)


def _resolve_string(text: str, variables: dict[str, Any]) -> Any:
    """Resolve a single string that may contain {placeholder} references.

    If the entire string is a single placeholder (e.g. '{query}'), the raw
    variable value is returned (preserving its type). Otherwise, standard
    string formatting is applied.
    """
    stripped = text.strip()

    # Exact single-placeholder: return the variable's raw value.
    if stripped.startswith("{") and stripped.endswith("}") and stripped.count("{") == 1:
        key = stripped[1:-1]
        return variables.get(key, text)

    # General case: substitute all placeholders via str.format_map.
    try:
        return text.format_map(_SafeFormatMap(variables))
    except (KeyError, ValueError):
        return text


class _SafeFormatMap(dict):  # type: ignore[type-arg]
    """A dict subclass that returns the original placeholder on missing keys."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"

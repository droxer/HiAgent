"""Skill loading, parsing, and registry."""

from __future__ import annotations

import os
import types
from dataclasses import dataclass
from typing import Any

import yaml
from loguru import logger


@dataclass(frozen=True)
class SkillStep:
    """Immutable description of a single step within a skill."""

    tool: str
    description: str
    input_template: dict[str, Any]
    condition: str | None = None


@dataclass(frozen=True)
class SkillManifest:
    """Immutable manifest describing a complete skill."""

    name: str
    description: str
    version: str = "1.0"
    tags: tuple[str, ...] = ()
    triggers: tuple[str, ...] = ()
    steps: tuple[SkillStep, ...] = ()


def _parse_step(raw: dict[str, Any]) -> SkillStep:
    """Parse a raw dict into an immutable SkillStep."""
    if "tool" not in raw:
        raise ValueError("Skill step missing required field: 'tool'")
    if "description" not in raw:
        raise ValueError("Skill step missing required field: 'description'")

    return SkillStep(
        tool=raw["tool"],
        description=raw["description"],
        input_template=types.MappingProxyType(dict(raw.get("input_template", {}))),
        condition=raw.get("condition"),
    )


def _parse_manifest(raw: dict[str, Any]) -> SkillManifest:
    """Parse a raw dict into an immutable SkillManifest."""
    if "name" not in raw:
        raise ValueError("Skill manifest missing required field: 'name'")
    if "description" not in raw:
        raise ValueError("Skill manifest missing required field: 'description'")

    raw_steps = raw.get("steps", [])
    steps = tuple(_parse_step(s) for s in raw_steps)

    return SkillManifest(
        name=raw["name"],
        description=raw["description"],
        version=str(raw.get("version", "1.0")),
        tags=tuple(raw.get("tags", ())),
        triggers=tuple(raw.get("triggers", ())),
        steps=steps,
    )


class SkillLoader:
    """Loads skill manifests from YAML files on disk."""

    _YAML_EXTENSIONS = (".yaml", ".yml")

    def __init__(self, skills_dir: str) -> None:
        self._skills_dir = skills_dir

    def load_all(self) -> tuple[SkillManifest, ...]:
        """Scan skills_dir for YAML files and parse each into a SkillManifest."""
        if not os.path.isdir(self._skills_dir):
            logger.warning("Skills directory does not exist: %s", self._skills_dir)
            return ()

        manifests: list[SkillManifest] = []
        for entry in sorted(os.listdir(self._skills_dir)):
            if not any(entry.endswith(ext) for ext in self._YAML_EXTENSIONS):
                continue
            path = os.path.join(self._skills_dir, entry)
            try:
                manifests.append(self.load_file(path))
            except Exception as exc:
                logger.error("Failed to load skill from %s: %s", path, exc)

        return tuple(manifests)

    def load_file(self, path: str) -> SkillManifest:
        """Parse a single YAML file into a SkillManifest."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Skill file not found: {path}")

        with open(path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)

        if not isinstance(raw, dict):
            raise ValueError(f"Invalid skill file (expected mapping): {path}")

        return _parse_manifest(raw)

    def watch(self) -> None:
        """Placeholder for hot-reload via file watcher.

        A future implementation could use watchdog or inotify to detect
        changes in skills_dir and reload affected manifests.
        """
        logger.info("Skill hot-reload watch requested (not yet implemented)")


class SkillRegistry:
    """Queryable, immutable-style registry of loaded skills."""

    def __init__(self, skills: tuple[SkillManifest, ...]) -> None:
        self._skills = skills
        self._by_name: dict[str, SkillManifest] = {s.name: s for s in skills}

    def find_by_name(self, name: str) -> SkillManifest | None:
        """Look up a skill by exact name."""
        return self._by_name.get(name)

    def find_by_trigger(self, text: str) -> tuple[SkillManifest, ...]:
        """Return skills whose triggers match keywords found in text."""
        lower_text = text.lower()
        matched = tuple(
            skill
            for skill in self._skills
            if any(trigger.lower() in lower_text for trigger in skill.triggers)
        )
        return matched

    def all_skills(self) -> tuple[SkillManifest, ...]:
        """Return all registered skills."""
        return self._skills

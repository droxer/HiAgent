"""Skill registry — queryable, immutable collection of discovered skills."""

from __future__ import annotations

import re

from loguru import logger

from agent.skills.models import SkillCatalogEntry, SkillContent

_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "for",
        "of",
        "to",
        "in",
        "on",
        "at",
        "by",
        "with",
        "from",
        "and",
        "or",
        "but",
        "not",
        "this",
        "that",
        "it",
        "as",
        "if",
        "when",
    }
)

_MATCH_THRESHOLD = 2

_WORD_RE = re.compile(r"\w+")


def _tokenize(text: str) -> set[str]:
    """Tokenize text into lowercase words, excluding stop words."""
    return {w for w in _WORD_RE.findall(text.lower()) if w not in _STOP_WORDS}


class SkillRegistry:
    """Immutable-style registry of loaded skills (SKILL.md format)."""

    def __init__(self, skills: tuple[SkillContent, ...] = ()) -> None:
        self._skills = skills
        self._by_name: dict[str, SkillContent] = {s.metadata.name: s for s in skills}

    def find_by_name(self, name: str) -> SkillContent | None:
        return self._by_name.get(name)

    def catalog(self) -> tuple[SkillCatalogEntry, ...]:
        return tuple(
            SkillCatalogEntry(
                name=s.metadata.name,
                description=s.metadata.description,
            )
            for s in self._skills
        )

    def match_description(self, text: str) -> SkillContent | None:
        """Match user text against skill descriptions and return the best match.

        Uses keyword overlap (excluding stop words). Returns the skill with
        the most matching words, or None if below threshold. Ties broken
        by insertion order (first registered wins).
        """
        if not text:
            return None

        user_words = _tokenize(text)
        if not user_words:
            return None

        best_skill: SkillContent | None = None
        best_count = 0

        for skill in self._skills:
            desc_words = _tokenize(skill.metadata.description)
            count = len(user_words & desc_words)
            if count > best_count:
                best_count = count
                best_skill = skill

        if best_count < _MATCH_THRESHOLD:
            return None

        return best_skill

    def catalog_prompt_section(self) -> str:
        """Format the skill catalog as XML for system prompt injection."""
        if not self._skills:
            return ""

        lines = [
            "\n<available_skills>",
            "When a task matches a skill's description, call the activate_skill tool",
            "with the skill's name to load its full instructions.",
            "",
        ]
        for skill in self._skills:
            meta = skill.metadata
            lines.append("<skill>")
            lines.append(f"  <name>{meta.name}</name>")
            lines.append(f"  <description>{meta.description}</description>")
            lines.append("</skill>")

        lines.append("</available_skills>")
        return "\n".join(lines)

    def all_skills(self) -> tuple[SkillContent, ...]:
        return self._skills

    def names(self) -> tuple[str, ...]:
        return tuple(self._by_name.keys())

    def add_skill(self, skill: SkillContent) -> SkillRegistry:
        """Return a new registry with the given skill added."""
        name = skill.metadata.name
        if name in self._by_name:
            logger.warning("Skill '{}' already registered, replacing", name)
            filtered = tuple(s for s in self._skills if s.metadata.name != name)
            return SkillRegistry((*filtered, skill))
        return SkillRegistry((*self._skills, skill))

    def remove_skill(self, name: str) -> SkillRegistry:
        """Return a new registry without the named skill."""
        filtered = tuple(s for s in self._skills if s.metadata.name != name)
        return SkillRegistry(filtered)

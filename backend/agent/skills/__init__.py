"""Skill system: discovery, registry, parsing, and installation."""

from agent.skills.discovery import SkillDiscoverer
from agent.skills.installer import SkillInstaller
from agent.skills.loader import SkillRegistry
from agent.skills.models import SkillCatalogEntry, SkillContent, SkillMetadata
from agent.skills.parser import parse_skill_md
from agent.skills.registry_client import SkillRegistryClient

__all__ = [
    "SkillCatalogEntry",
    "SkillContent",
    "SkillDiscoverer",
    "SkillInstaller",
    "SkillMetadata",
    "SkillRegistry",
    "SkillRegistryClient",
    "parse_skill_md",
]

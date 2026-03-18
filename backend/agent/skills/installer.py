"""Skill installer — install skills from git repos, URLs, or archives."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlparse

import httpx
from loguru import logger

from agent.skills.models import SkillCatalogEntry, SkillContent
from agent.skills.parser import parse_skill_md

_MAX_DOWNLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
_GIT_TIMEOUT = 30  # seconds


class SkillInstaller:
    """Installs, uninstalls, and lists user-installed skills."""

    def __init__(self, install_dir: str | None = None) -> None:
        self._install_dir = install_dir or os.path.join(
            str(Path.home()), ".hiagent", "skills"
        )
        os.makedirs(self._install_dir, exist_ok=True)

    @property
    def install_dir(self) -> str:
        return self._install_dir

    async def install_from_git(
        self,
        repo_url: str,
        skill_path: str | None = None,
    ) -> SkillContent:
        """Clone a git repo and install a skill from it.

        Parameters
        ----------
        repo_url:
            HTTPS git URL (e.g. https://github.com/user/repo.git).
        skill_path:
            Optional subdirectory within the repo containing the SKILL.md.
            If None, the repo root is assumed.

        Returns
        -------
        The installed SkillContent.

        Raises
        ------
        ValueError for invalid URLs or missing SKILL.md.
        RuntimeError for git clone failures.
        """
        _validate_https_url(repo_url)

        with tempfile.TemporaryDirectory() as tmp_dir:
            clone_dir = os.path.join(tmp_dir, "repo")
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, clone_dir],
                    check=True,
                    capture_output=True,
                    timeout=_GIT_TIMEOUT,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(
                    f"Git clone timed out after {_GIT_TIMEOUT}s"
                ) from exc
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    f"Git clone failed: {exc.stderr.decode(errors='replace')}"
                ) from exc

            # Locate SKILL.md
            skill_dir = clone_dir
            if skill_path:
                skill_dir = os.path.join(clone_dir, skill_path)

            skill_file = os.path.join(skill_dir, "SKILL.md")
            if not os.path.isfile(skill_file):
                raise ValueError(f"SKILL.md not found at {skill_path or 'repo root'}")

            skill = parse_skill_md(skill_file)
            return self._install_skill_dir(skill_dir, skill)

    async def install_from_url(self, url: str) -> SkillContent:
        """Download a SKILL.md or archive from a URL and install it.

        Supports direct SKILL.md files and .zip archives.

        Raises
        ------
        ValueError for invalid URLs or content.
        RuntimeError for download failures.
        """
        _validate_https_url(url)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

            content_length = len(response.content)
            if content_length > _MAX_DOWNLOAD_SIZE:
                raise ValueError(
                    f"Download too large: {content_length} bytes (max {_MAX_DOWNLOAD_SIZE})"
                )

        with tempfile.TemporaryDirectory() as tmp_dir:
            if url.endswith(".zip"):
                archive_path = os.path.join(tmp_dir, "skill.zip")
                with open(archive_path, "wb") as f:
                    f.write(response.content)

                extract_dir = os.path.join(tmp_dir, "extracted")
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(extract_dir)

                # Find SKILL.md in extracted content
                skill_file = _find_skill_md(extract_dir)
                if not skill_file:
                    raise ValueError("No SKILL.md found in archive")

                skill = parse_skill_md(skill_file)
                return self._install_skill_dir(os.path.dirname(skill_file), skill)

            # Assume direct SKILL.md file
            skill_dir = os.path.join(tmp_dir, "skill")
            os.makedirs(skill_dir, exist_ok=True)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            with open(skill_file, "w", encoding="utf-8") as f:
                f.write(response.text)

            skill = parse_skill_md(skill_file)
            return self._install_skill_dir(skill_dir, skill)

    def uninstall(self, name: str) -> bool:
        """Remove an installed skill by name. Returns True if removed."""
        name = _sanitize_name(name)
        target = os.path.join(self._install_dir, name)
        if os.path.isdir(target):
            shutil.rmtree(target)
            logger.info("Uninstalled skill '{}'", name)
            return True
        return False

    def list_installed(self) -> tuple[SkillCatalogEntry, ...]:
        """List all user-installed skills."""
        entries: list[SkillCatalogEntry] = []

        if not os.path.isdir(self._install_dir):
            return ()

        for entry_name in sorted(os.listdir(self._install_dir)):
            skill_dir = os.path.join(self._install_dir, entry_name)
            skill_file = os.path.join(skill_dir, "SKILL.md")
            if not os.path.isfile(skill_file):
                continue
            try:
                skill = parse_skill_md(skill_file)
                entries.append(
                    SkillCatalogEntry(
                        name=skill.metadata.name,
                        description=skill.metadata.description,
                    )
                )
            except Exception as exc:
                logger.error("Failed to parse installed skill {}: {}", entry_name, exc)

        return tuple(entries)

    def _install_skill_dir(self, source_dir: str, skill: SkillContent) -> SkillContent:
        """Copy a skill directory into the install location."""
        name = _sanitize_name(skill.metadata.name)
        target = os.path.join(self._install_dir, name)

        # Remove existing if present
        if os.path.exists(target):
            shutil.rmtree(target)

        shutil.copytree(source_dir, target, ignore=shutil.ignore_patterns(".git"))
        logger.info("Installed skill '{}' to {}", name, target)

        # Re-parse from installed location and tag as user-installed
        installed = parse_skill_md(os.path.join(target, "SKILL.md"))
        return replace(installed, source_type="user")


def _validate_https_url(url: str) -> None:
    """Validate that a URL uses HTTPS."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Only HTTPS URLs are allowed, got: {parsed.scheme}")
    if not parsed.netloc:
        raise ValueError("Invalid URL: no host specified")


def _sanitize_name(name: str) -> str:
    """Sanitize a skill name for use as a directory name."""
    # Allow only alphanumeric and hyphens
    sanitized = "".join(c if c.isalnum() or c == "-" else "-" for c in name)
    return sanitized.strip("-") or "unnamed-skill"


def _find_skill_md(root: str) -> str | None:
    """Find the first SKILL.md file in a directory tree."""
    for dirpath, _dirs, files in os.walk(root):
        if "SKILL.md" in files:
            return os.path.join(dirpath, "SKILL.md")
    return None

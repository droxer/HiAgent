"""Artifact management for extracting files from sandboxes.

Provides an ``ArtifactManager`` that downloads files from sandbox
sessions to local storage and tracks metadata. All data structures
are immutable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from loguru import logger

from agent.sandbox.base import SandboxSession


@dataclass(frozen=True)
class Artifact:
    """Immutable metadata for a file extracted from a sandbox.

    Attributes:
        path: Relative path within the storage directory.
        content_type: MIME type or generic type label.
        size: File size in bytes.
        source_agent_id: ID of the agent that produced the artifact.
    """

    path: str
    content_type: str
    size: int
    source_agent_id: str | None = None


# ---------------------------------------------------------------------------
# Content-type inference (pure function)
# ---------------------------------------------------------------------------

_EXTENSION_CONTENT_TYPES: dict[str, str] = {
    ".py": "text/x-python",
    ".js": "text/javascript",
    ".ts": "text/typescript",
    ".json": "application/json",
    ".csv": "text/csv",
    ".html": "text/html",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
}


def _infer_content_type(path: str) -> str:
    """Infer a content type from the file extension."""
    _, ext = os.path.splitext(path)
    return _EXTENSION_CONTENT_TYPES.get(ext.lower(), "application/octet-stream")


# ---------------------------------------------------------------------------
# ArtifactManager
# ---------------------------------------------------------------------------


class ArtifactManager:
    """Manages extraction and storage of sandbox artifacts.

    Downloads files from sandbox sessions to a local directory
    and provides metadata access.
    """

    def __init__(self, storage_dir: str = "./artifacts") -> None:
        self._storage_dir = storage_dir

    async def extract_from_sandbox(
        self,
        session: SandboxSession,
        remote_paths: list[str],
        agent_id: str | None = None,
    ) -> tuple[Artifact, ...]:
        """Download files from *session* and return artifact metadata.

        Args:
            session: An active sandbox session.
            remote_paths: List of file paths inside the sandbox.
            agent_id: Optional ID of the agent that produced the files.

        Returns:
            A tuple of ``Artifact`` objects for successfully downloaded files.
        """
        os.makedirs(self._storage_dir, exist_ok=True)
        artifacts: list[Artifact] = []

        for remote_path in remote_paths:
            artifact = await self._extract_single(
                session,
                remote_path,
                agent_id,
            )
            if artifact is not None:
                artifacts.append(artifact)

        return tuple(artifacts)

    async def list_artifacts(self) -> tuple[Artifact, ...]:
        """List all artifacts currently in the storage directory."""
        if not os.path.isdir(self._storage_dir):
            return ()

        artifacts: list[Artifact] = []
        for entry in os.scandir(self._storage_dir):
            if entry.is_file():
                artifact = Artifact(
                    path=entry.name,
                    content_type=_infer_content_type(entry.name),
                    size=entry.stat().st_size,
                )
                artifacts.append(artifact)

        return tuple(artifacts)

    def get_path(self, artifact: Artifact) -> str:
        """Return the full local filesystem path for *artifact*."""
        return os.path.join(self._storage_dir, artifact.path)

    async def _extract_single(
        self,
        session: SandboxSession,
        remote_path: str,
        agent_id: str | None,
    ) -> Artifact | None:
        """Download a single file, returning its Artifact or None on error."""
        file_name = os.path.basename(remote_path)
        if not file_name:
            logger.warning("Skipping empty filename from path: %s", remote_path)
            return None

        local_path = os.path.join(self._storage_dir, file_name)

        try:
            await session.download_file(remote_path, local_path)
        except FileNotFoundError:
            logger.warning("Remote file not found: %s", remote_path)
            return None
        except Exception as exc:
            logger.error("Failed to download '%s': %s", remote_path, exc)
            return None

        size = os.path.getsize(local_path)
        return Artifact(
            path=file_name,
            content_type=_infer_content_type(file_name),
            size=size,
            source_agent_id=agent_id,
        )

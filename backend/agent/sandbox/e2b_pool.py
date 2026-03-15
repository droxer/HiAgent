"""Sandbox pool for reusing paused E2B sandboxes across conversations."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from loguru import logger

from agent.sandbox.base import PoolKey, SandboxConfig


@dataclass(frozen=True)
class _PoolEntry:
    """A paused sandbox waiting to be reused."""

    sandbox_id: str
    paused_at: float  # time.monotonic()
    config: SandboxConfig


class SandboxPool:
    """Pool of paused E2B sandboxes for reuse.

    Sandboxes are keyed by (template, env_vars) so only compatible
    environments are matched. Stale entries (older than ``max_idle_seconds``)
    are discarded on acquire.
    """

    def __init__(
        self,
        api_key: str,
        max_per_key: int = 3,
        max_idle_seconds: int = 600,
    ) -> None:
        self._api_key = api_key
        self._max_per_key = max_per_key
        self._max_idle_seconds = max_idle_seconds
        self._entries: dict[PoolKey, list[_PoolEntry]] = defaultdict(list)
        self._lock = asyncio.Lock()

    @staticmethod
    def _key_for(config: SandboxConfig) -> PoolKey:
        return PoolKey(template=config.template, env_vars=config.env_vars)

    async def acquire(self, config: SandboxConfig) -> Any:
        """Try to reconnect to a pooled sandbox matching *config*.

        Returns an ``E2BSession`` on success, or ``None`` if no suitable
        sandbox is available.
        """
        key = self._key_for(config)
        now = time.monotonic()

        async with self._lock:
            entries = self._entries.get(key)
            if not entries:
                return None

            while entries:
                entry = entries.pop()
                age = now - entry.paused_at
                if age > self._max_idle_seconds:
                    logger.debug(
                        "Discarding stale pooled sandbox %s (age=%.0fs)",
                        entry.sandbox_id,
                        age,
                    )
                    continue

                # Try to reconnect
                try:
                    session = await self._connect(entry)
                    logger.info(
                        "Reused pooled E2B sandbox %s (idle=%.0fs)",
                        entry.sandbox_id,
                        age,
                    )
                    return session
                except Exception as exc:
                    logger.warning(
                        "Failed to reconnect pooled sandbox %s: %s",
                        entry.sandbox_id,
                        exc,
                    )
                    continue

        return None

    async def _connect(self, entry: _PoolEntry) -> Any:
        """Reconnect to a paused sandbox and return an E2BSession."""
        from agent.sandbox.e2b_provider import E2BSession, _import_e2b

        SandboxClass = _import_e2b()
        sandbox = await asyncio.to_thread(
            SandboxClass.connect,
            entry.sandbox_id,
            api_key=self._api_key,
        )
        return E2BSession(sandbox=sandbox, config=entry.config)

    async def release(self, session: Any) -> None:
        """Pause *session* and add it to the pool (or kill if pool is full)."""
        from agent.sandbox.e2b_provider import E2BSession

        if not isinstance(session, E2BSession):
            await session.close()
            return

        sandbox_id = session.sandbox_id
        config = session._config
        if sandbox_id is None or config is None:
            await session.kill()
            return

        key = self._key_for(config)

        async with self._lock:
            if len(self._entries[key]) >= self._max_per_key:
                logger.debug(
                    "Pool full for key %s, killing sandbox %s",
                    key,
                    sandbox_id,
                )
                await session.kill()
                return

        # Pause the sandbox so it can be resumed later
        await session.close()

        async with self._lock:
            self._entries[key].append(
                _PoolEntry(
                    sandbox_id=sandbox_id,
                    paused_at=time.monotonic(),
                    config=config,
                )
            )
        logger.info("Pooled sandbox %s for key %s", sandbox_id, key)

    async def drain(self) -> None:
        """Kill all pooled sandboxes. Called on application shutdown."""
        from agent.sandbox.e2b_provider import _import_e2b

        async with self._lock:
            all_entries: list[_PoolEntry] = []
            for entries in self._entries.values():
                all_entries.extend(entries)
            self._entries.clear()

        for entry in all_entries:
            try:
                SandboxClass = _import_e2b()
                sandbox = await asyncio.to_thread(
                    SandboxClass.connect,
                    entry.sandbox_id,
                    api_key=self._api_key,
                )
                await asyncio.to_thread(sandbox.kill)
                logger.info("Drained pooled sandbox %s", entry.sandbox_id)
            except Exception as exc:
                logger.warning(
                    "Failed to drain sandbox %s: %s", entry.sandbox_id, exc
                )

        logger.info("Sandbox pool drained (%d sandboxes)", len(all_entries))

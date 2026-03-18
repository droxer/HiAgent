"""Tests for Phase 3: Sandbox pooling."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from agent.sandbox.base import PoolKey, SandboxConfig
from agent.sandbox.e2b_pool import SandboxPool, _PoolEntry


@pytest.fixture
def pool() -> SandboxPool:
    return SandboxPool(api_key="test-key", max_per_key=2, max_idle_seconds=60)


@pytest.fixture
def config() -> SandboxConfig:
    return SandboxConfig(template="default")


class TestPoolKeyGeneration:
    def test_key_from_config(self, pool: SandboxPool) -> None:
        config = SandboxConfig(template="default", env_vars=(("A", "1"),))
        key = pool._key_for(config)
        assert key == PoolKey(template="default", env_vars=(("A", "1"),))


class TestAcquire:
    @pytest.mark.asyncio
    async def test_returns_none_when_empty(
        self, pool: SandboxPool, config: SandboxConfig
    ) -> None:
        result = await pool.acquire(config)
        assert result is None

    @pytest.mark.asyncio
    async def test_skips_stale_entries(
        self, pool: SandboxPool, config: SandboxConfig
    ) -> None:
        key = pool._key_for(config)
        pool._entries[key].append(
            _PoolEntry(
                sandbox_id="stale-1",
                paused_at=time.monotonic() - 9999,
                config=config,
            )
        )
        result = await pool.acquire(config)
        assert result is None
        assert len(pool._entries[key]) == 0

    @pytest.mark.asyncio
    async def test_returns_session_on_successful_connect(
        self, pool: SandboxPool, config: SandboxConfig
    ) -> None:
        key = pool._key_for(config)
        pool._entries[key].append(
            _PoolEntry(
                sandbox_id="good-1",
                paused_at=time.monotonic(),
                config=config,
            )
        )

        fake_sandbox = MagicMock()
        fake_sandbox.sandbox_id = "good-1"
        fake_sandbox.commands.run.return_value = MagicMock(
            exit_code=0, stdout="", stderr=""
        )

        with patch(
            "agent.sandbox.e2b_provider._import_e2b"
        ) as mock_import:
            mock_cls = MagicMock()
            mock_cls.connect.return_value = fake_sandbox
            mock_import.return_value = mock_cls

            result = await pool.acquire(config)
            assert result is not None
            assert result.sandbox_id == "good-1"
            fake_sandbox.commands.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_failed_connect(
        self, pool: SandboxPool, config: SandboxConfig
    ) -> None:
        key = pool._key_for(config)
        pool._entries[key].append(
            _PoolEntry(
                sandbox_id="dead-1",
                paused_at=time.monotonic(),
                config=config,
            )
        )

        with patch(
            "agent.sandbox.e2b_provider._import_e2b"
        ) as mock_import:
            mock_cls = MagicMock()
            mock_cls.connect.side_effect = RuntimeError("sandbox gone")
            mock_import.return_value = mock_cls

            result = await pool.acquire(config)
            assert result is None

    @pytest.mark.asyncio
    async def test_scrubs_uploads_before_reuse(
        self, pool: SandboxPool, config: SandboxConfig
    ) -> None:
        key = pool._key_for(config)
        pool._entries[key].append(
            _PoolEntry(
                sandbox_id="clean-1",
                paused_at=time.monotonic(),
                config=config,
            )
        )

        fake_sandbox = MagicMock()
        fake_sandbox.sandbox_id = "clean-1"
        fake_sandbox.commands.run.return_value = MagicMock(
            exit_code=0, stdout="", stderr=""
        )

        with patch("agent.sandbox.e2b_provider._import_e2b") as mock_import:
            mock_cls = MagicMock()
            mock_cls.connect.return_value = fake_sandbox
            mock_import.return_value = mock_cls

            await pool.acquire(config)

        scrub_command = fake_sandbox.commands.run.call_args.args[0]
        assert "rm -rf /home/user/uploads" in scrub_command
        assert "mkdir -p /home/user/uploads" in scrub_command


class TestRelease:
    @pytest.mark.asyncio
    async def test_adds_to_pool(
        self, pool: SandboxPool, config: SandboxConfig
    ) -> None:
        from agent.sandbox.e2b_provider import E2BSession

        fake_sandbox = MagicMock()
        fake_sandbox.sandbox_id = "release-1"
        fake_sandbox.pause = MagicMock()
        session = E2BSession(sandbox=fake_sandbox, config=config)

        await pool.release(session)

        key = pool._key_for(config)
        assert len(pool._entries[key]) == 1
        assert pool._entries[key][0].sandbox_id == "release-1"

    @pytest.mark.asyncio
    async def test_kills_when_pool_full(
        self, pool: SandboxPool, config: SandboxConfig
    ) -> None:
        from agent.sandbox.e2b_provider import E2BSession

        key = pool._key_for(config)
        # Fill pool to max (2)
        for i in range(2):
            pool._entries[key].append(
                _PoolEntry(
                    sandbox_id=f"existing-{i}",
                    paused_at=time.monotonic(),
                    config=config,
                )
            )

        fake_sandbox = MagicMock()
        fake_sandbox.sandbox_id = "overflow-1"
        fake_sandbox.kill = MagicMock()
        session = E2BSession(sandbox=fake_sandbox, config=config)

        await pool.release(session)

        # Should still be 2, not 3
        assert len(pool._entries[key]) == 2
        fake_sandbox.kill.assert_called_once()


class TestDrain:
    @pytest.mark.asyncio
    async def test_drain_clears_all(
        self, pool: SandboxPool, config: SandboxConfig
    ) -> None:
        key = pool._key_for(config)
        pool._entries[key].append(
            _PoolEntry(
                sandbox_id="drain-1",
                paused_at=time.monotonic(),
                config=config,
            )
        )

        fake_sandbox = MagicMock()
        fake_sandbox.kill = MagicMock()

        with patch(
            "agent.sandbox.e2b_provider._import_e2b"
        ) as mock_import:
            mock_cls = MagicMock()
            mock_cls.connect.return_value = fake_sandbox
            mock_import.return_value = mock_cls

            await pool.drain()

        assert len(pool._entries) == 0
        fake_sandbox.kill.assert_called_once()

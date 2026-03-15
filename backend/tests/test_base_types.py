"""Tests for Phase 1: base data types and protocol extensions."""

from __future__ import annotations

from agent.sandbox.base import (
    CodeOutput,
    CodeResult,
    ExecResult,
    ExtendedSandboxSession,
    PoolKey,
    SandboxSession,
    StreamCallback,
)


class TestCodeOutput:
    def test_frozen(self) -> None:
        out = CodeOutput(mime_type="image/png", data="abc", display_type="image")
        assert out.mime_type == "image/png"
        assert out.data == "abc"
        assert out.display_type == "image"

    def test_equality(self) -> None:
        a = CodeOutput(mime_type="text/plain", data="x", display_type="text")
        b = CodeOutput(mime_type="text/plain", data="x", display_type="text")
        assert a == b


class TestCodeResult:
    def test_frozen(self) -> None:
        outputs = (CodeOutput(mime_type="text/plain", data="hi", display_type="text"),)
        result = CodeResult(stdout="out", stderr="", error=None, results=outputs)
        assert result.stdout == "out"
        assert result.error is None
        assert len(result.results) == 1

    def test_with_error(self) -> None:
        result = CodeResult(stdout="", stderr="err", error="failed", results=())
        assert result.error == "failed"


class TestPoolKey:
    def test_frozen_and_hashable(self) -> None:
        key = PoolKey(template="default", env_vars=(("A", "1"),))
        assert hash(key) is not None

    def test_equality(self) -> None:
        a = PoolKey(template="default", env_vars=())
        b = PoolKey(template="default", env_vars=())
        assert a == b

    def test_different_envs(self) -> None:
        a = PoolKey(template="default", env_vars=(("A", "1"),))
        b = PoolKey(template="default", env_vars=(("B", "2"),))
        assert a != b


class TestStreamCallback:
    def test_type_alias(self) -> None:
        def cb(s: str) -> None:
            pass

        # StreamCallback is just a type alias, not instantiable
        _: StreamCallback = cb


class TestExtendedSandboxSession:
    def test_is_runtime_checkable(self) -> None:
        assert isinstance(ExtendedSandboxSession, type)

    def test_basic_session_is_not_extended(self) -> None:
        class BasicSession:
            async def exec(self, command, timeout=None, workdir=None):
                return ExecResult(stdout="", stderr="", exit_code=0)

            async def read_file(self, path):
                return ""

            async def write_file(self, path, content):
                pass

            async def upload_file(self, local_path, remote_path):
                pass

            async def download_file(self, remote_path, local_path):
                pass

            async def close(self):
                pass

        session = BasicSession()
        assert isinstance(session, SandboxSession)
        assert not isinstance(session, ExtendedSandboxSession)

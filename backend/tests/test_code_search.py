"""Tests for code search tools."""

from __future__ import annotations

from agent.tools.base import ExecutionContext
from agent.tools.sandbox.code_search import FileGlob, FileSearch


class TestFileGlob:
    def test_definition(self) -> None:
        tool = FileGlob()
        defn = tool.definition()
        assert defn.name == "file_glob"
        assert defn.execution_context == ExecutionContext.SANDBOX
        assert "pattern" in defn.input_schema["required"]

    async def test_empty_pattern_fails(self) -> None:
        tool = FileGlob()

        class MockSession:
            pass

        result = await tool.execute(session=MockSession(), pattern="")
        assert not result.success
        assert "empty" in result.error.lower()

    async def test_whitespace_pattern_fails(self) -> None:
        tool = FileGlob()

        class MockSession:
            pass

        result = await tool.execute(session=MockSession(), pattern="   ")
        assert not result.success
        assert "empty" in result.error.lower()


class TestFileSearch:
    def test_definition(self) -> None:
        tool = FileSearch()
        defn = tool.definition()
        assert defn.name == "file_search"
        assert defn.execution_context == ExecutionContext.SANDBOX
        assert "pattern" in defn.input_schema["required"]

    async def test_empty_pattern_fails(self) -> None:
        tool = FileSearch()

        class MockSession:
            pass

        result = await tool.execute(session=MockSession(), pattern="")
        assert not result.success

    async def test_whitespace_pattern_fails(self) -> None:
        tool = FileSearch()

        class MockSession:
            pass

        result = await tool.execute(session=MockSession(), pattern="  ")
        assert not result.success

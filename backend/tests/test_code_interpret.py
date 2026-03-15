"""Tests for Phase 4: Code interpreter tool."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.sandbox.base import CodeOutput, CodeResult
from agent.tools.sandbox.code_interpret import CodeInterpret


@pytest.fixture
def tool() -> CodeInterpret:
    return CodeInterpret()


class TestDefinition:
    def test_name(self, tool: CodeInterpret) -> None:
        assert tool.definition().name == "code_interpret"

    def test_required_fields(self, tool: CodeInterpret) -> None:
        schema = tool.definition().input_schema
        assert "code" in schema["required"]


class TestExecute:
    @pytest.mark.asyncio
    async def test_empty_code(self, tool: CodeInterpret) -> None:
        session = MagicMock()
        result = await tool.execute(session=session, code="")
        assert not result.success
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_non_extended_session(self, tool: CodeInterpret) -> None:
        session = MagicMock(spec=[])  # No ExtendedSandboxSession methods
        result = await tool.execute(session=session, code="print(1)")
        assert not result.success
        assert "not supported" in result.error.lower()

    @pytest.mark.asyncio
    async def test_successful_execution(self, tool: CodeInterpret) -> None:
        code_result = CodeResult(
            stdout="42",
            stderr="",
            error=None,
            results=(
                CodeOutput(mime_type="text/plain", data="42", display_type="text"),
            ),
        )

        session = MagicMock()
        session.run_code = AsyncMock(return_value=code_result)
        session.exec = AsyncMock()
        session.read_file = AsyncMock()
        session.write_file = AsyncMock()
        session.upload_file = AsyncMock()
        session.download_file = AsyncMock()
        session.close = AsyncMock()
        session.exec_stream = AsyncMock()
        session.sandbox_id = "test"

        result = await tool.execute(session=session, code="print(42)")

        assert result.success
        assert "42" in result.output
        assert result.metadata["rich_outputs"][0]["mime_type"] == "text/plain"

    @pytest.mark.asyncio
    async def test_execution_with_error(self, tool: CodeInterpret) -> None:
        code_result = CodeResult(
            stdout="",
            stderr="traceback...",
            error="NameError: x",
            results=(),
        )

        session = MagicMock()
        session.run_code = AsyncMock(return_value=code_result)
        session.exec = AsyncMock()
        session.read_file = AsyncMock()
        session.write_file = AsyncMock()
        session.upload_file = AsyncMock()
        session.download_file = AsyncMock()
        session.close = AsyncMock()
        session.exec_stream = AsyncMock()
        session.sandbox_id = "test"

        result = await tool.execute(session=session, code="x")

        assert result.success  # tool itself didn't fail, code had error
        assert result.metadata["has_error"] is True
        assert "NameError" in result.output

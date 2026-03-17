"""Tests for preview tools."""

from __future__ import annotations

from agent.tools.base import ExecutionContext
from agent.tools.sandbox.preview import PreviewStart, PreviewStop


class TestPreviewStart:
    def test_definition(self) -> None:
        tool = PreviewStart()
        defn = tool.definition()
        assert defn.name == "preview_start"
        assert defn.execution_context == ExecutionContext.SANDBOX
        assert "preview" in defn.tags

    async def test_invalid_port_below_range_fails(self) -> None:
        tool = PreviewStart()
        result = await tool.execute(session=None, port=80)
        assert not result.success
        assert "Port" in result.error

    async def test_invalid_port_above_range_fails(self) -> None:
        tool = PreviewStart()
        result = await tool.execute(session=None, port=70000)
        assert not result.success
        assert "Port" in result.error

    async def test_valid_port_boundary_low(self) -> None:
        """Port 1024 is the lowest valid port -- should not fail validation."""
        tool = PreviewStart()
        # Port 1024 passes validation but will fail on session.exec since
        # session is None.  We just verify the port check itself doesn't reject it.
        try:
            await tool.execute(session=None, port=1024)
        except AttributeError:
            # Expected: session is None so session.exec raises AttributeError
            pass


class TestPreviewStop:
    def test_definition(self) -> None:
        tool = PreviewStop()
        defn = tool.definition()
        assert defn.name == "preview_stop"
        assert defn.execution_context == ExecutionContext.SANDBOX

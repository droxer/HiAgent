"""Tests for extended thinking support."""

from __future__ import annotations

from agent.llm.client import LLMResponse, TokenUsage, _extract_thinking


class TestLLMResponseThinking:
    def test_default_empty_thinking(self) -> None:
        r = LLMResponse(
            text="hello",
            tool_calls=(),
            stop_reason="end_turn",
            usage=TokenUsage(input_tokens=10, output_tokens=5),
        )
        assert r.thinking == ""

    def test_with_thinking(self) -> None:
        r = LLMResponse(
            text="hello",
            tool_calls=(),
            stop_reason="end_turn",
            usage=TokenUsage(input_tokens=10, output_tokens=5),
            thinking="Let me think...",
        )
        assert r.thinking == "Let me think..."

    def test_frozen(self) -> None:
        r = LLMResponse(
            text="hi",
            tool_calls=(),
            stop_reason="end_turn",
            usage=TokenUsage(input_tokens=1, output_tokens=1),
            thinking="thought",
        )
        import dataclasses

        assert dataclasses.is_dataclass(r)
        # Verify frozen
        try:
            r.thinking = "new"  # type: ignore[misc]
            assert False, "Should have raised"
        except AttributeError:
            pass


class TestExtractThinking:
    def test_empty_content(self) -> None:
        assert _extract_thinking([]) == ""

    def test_no_thinking_blocks(self) -> None:
        class TextBlock:
            type = "text"
            text = "hello"

        assert _extract_thinking([TextBlock()]) == ""

    def test_with_thinking_block(self) -> None:
        class ThinkingBlock:
            type = "thinking"
            thinking = "Let me reason..."

        assert _extract_thinking([ThinkingBlock()]) == "Let me reason..."

    def test_multiple_thinking_blocks(self) -> None:
        class ThinkingBlock:
            type = "thinking"

            def __init__(self, text: str) -> None:
                self.thinking = text

        blocks = [ThinkingBlock("First."), ThinkingBlock(" Second.")]
        assert _extract_thinking(blocks) == "First. Second."

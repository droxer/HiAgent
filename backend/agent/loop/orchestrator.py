"""Single-agent ReAct loop orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from loguru import logger

from agent.llm.client import ClaudeClient
from agent.loop.helpers import (
    apply_response_to_state,
    extract_final_text,
    process_tool_calls,
)
from agent.loop.observer import Observer
from agent.tools.executor import ToolExecutor
from agent.tools.registry import ToolRegistry
from api.events import EventEmitter, EventType


@dataclass(frozen=True)
class AgentState:
    """Immutable state of an agent execution loop.

    All mutation methods return a new AgentState instance,
    leaving the original unchanged.
    """

    messages: tuple[dict[str, Any], ...] = ()
    iteration: int = 0
    completed: bool = False
    error: str | None = None

    def add_message(self, message: dict[str, Any]) -> AgentState:
        """Return new state with message appended."""
        return replace(self, messages=(*self.messages, message))

    def increment_iteration(self) -> AgentState:
        """Return new state with iteration incremented by one."""
        return replace(self, iteration=self.iteration + 1)

    def mark_completed(self, summary: str) -> AgentState:
        """Return new state marked as completed with a summary message."""
        final_msg: dict[str, Any] = {"role": "assistant", "content": summary}
        return replace(
            self,
            messages=(*self.messages, final_msg),
            completed=True,
        )

    def mark_error(self, error: str) -> AgentState:
        """Return new state marked as failed with an error message."""
        return replace(self, error=error)


class AgentOrchestrator:
    """Runs a single-agent ReAct loop until completion or max iterations."""

    def __init__(
        self,
        claude_client: ClaudeClient,
        tool_registry: ToolRegistry,
        tool_executor: ToolExecutor,
        event_emitter: EventEmitter,
        system_prompt: str,
        max_iterations: int = 50,
        observer: Observer | None = None,
    ) -> None:
        if not system_prompt:
            raise ValueError("system_prompt must not be empty")
        self._client = claude_client
        self._registry = tool_registry
        self._executor = tool_executor
        self._emitter = event_emitter
        self._system_prompt = system_prompt
        self._max_iterations = max_iterations
        self._observer = observer or Observer()
        self._task_complete_summary: str | None = None
        self._state = AgentState()

    async def on_task_complete(self, summary: str) -> None:
        """Callback for the task_complete tool."""
        self._task_complete_summary = summary

    async def run(self, user_message: str) -> str:
        """Execute the agent loop and return the final text response."""
        if not user_message.strip():
            raise ValueError("user_message must not be empty")

        logger.info("turn_start user_message_length={}", len(user_message))

        await self._emitter.emit(
            EventType.TURN_START,
            {"message": user_message},
        )

        # Append user message to existing state (preserves conversation history)
        self._state = self._state.add_message(
            {"role": "user", "content": user_message},
        )
        # Reset completion flags for the new turn
        self._task_complete_summary = None
        self._state = replace(self._state, completed=False, error=None, iteration=0)

        tools = self._registry.to_anthropic_tools()

        while not self._state.completed and self._state.error is None:
            self._state = self._state.increment_iteration()
            self._state = await self._run_iteration(self._state, tools)

        logger.info("turn_complete iterations={}", self._state.iteration)

        if self._state.error:
            await self._emitter.emit(
                EventType.TASK_ERROR,
                {"error": self._state.error},
            )
            return f"Error: {self._state.error}"

        final_text = extract_final_text(self._state)
        await self._emitter.emit(
            EventType.TURN_COMPLETE,
            {"result": final_text},
        )
        return final_text

    async def _run_iteration(
        self,
        state: AgentState,
        tools: list[dict[str, Any]],
    ) -> AgentState:
        """Run a single iteration of the ReAct loop."""
        # Compact message history before the LLM call if needed
        if self._observer.should_compact(state.messages):
            logger.debug("compacting_message_history")
            compacted = self._observer.compact(state.messages)
            state = replace(state, messages=compacted)

        logger.info("iteration={}/{}", state.iteration, self._max_iterations)

        await self._emitter.emit(
            EventType.ITERATION_START,
            {"iteration": state.iteration},
            iteration=state.iteration,
        )

        if state.iteration > self._max_iterations:
            logger.warning("max_iterations_exceeded limit={}", self._max_iterations)
            return state.mark_error(
                f"Exceeded maximum iterations ({self._max_iterations})",
            )

        try:
            async def _on_text_delta(delta: str) -> None:
                await self._emitter.emit(
                    EventType.TEXT_DELTA,
                    {"delta": delta},
                    iteration=state.iteration,
                )

            response = await self._client.create_message_stream(
                system=self._system_prompt,
                messages=list(state.messages),
                tools=tools if tools else None,
                on_text_delta=_on_text_delta,
            )
        except Exception as exc:
            logger.error("llm_call_failed error={}", exc)
            return state.mark_error(f"LLM call failed: {exc}")

        logger.info(
            "llm_response stop_reason={} tool_calls={} input_tokens={} output_tokens={}",
            response.stop_reason,
            len(response.tool_calls),
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

        await self._emitter.emit(
            EventType.LLM_RESPONSE,
            {
                "text": response.text,
                "tool_call_count": len(response.tool_calls),
                "stop_reason": response.stop_reason,
                "usage": response.usage,
            },
            iteration=state.iteration,
        )

        state = apply_response_to_state(state, response)

        if not response.tool_calls:
            return state.mark_completed(response.text)

        state = await process_tool_calls(
            state=state,
            tool_calls=response.tool_calls,
            executor=self._executor,
            emitter=self._emitter,
            stop_check=lambda: self._task_complete_summary is not None,
        )

        # Check if task_complete tool was invoked during tool processing
        if self._task_complete_summary is not None:
            return state.mark_completed(self._task_complete_summary)

        return state

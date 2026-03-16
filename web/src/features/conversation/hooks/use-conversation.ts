"use client";

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { useAppStore } from "@/shared/stores";
import {
  createConversation,
  sendFollowUpMessage,
} from "../api/conversation-api";
import type { AgentEvent, AssistantPhase, ChatMessage, TaskState } from "@/shared/types";

export function useConversation(
  assistantMessages: ChatMessage[],
  taskState: TaskState,
  events: AgentEvent[] = [],
  assistantPhase: AssistantPhase,
) {
  const [userMessages, setUserMessages] = useState<ChatMessage[]>([]);
  const [isWaitingForAgent, setIsWaitingForAgent] = useState(false);
  const eventCountAtSendRef = useRef(events.length);

  const {
    conversationId,
    isLiveConversation,
    startConversation,
    switchConversation,
    resumeConversation,
    updateConversationTitle,
    resetConversation,
  } = useAppStore();

  // Clear waiting state only when NEW events arrive (after send) and
  // the assistant has actually started responding. This prevents the
  // skeleton from being immediately cleared by stale events from prior turns.
  useEffect(() => {
    if (!isWaitingForAgent) return;
    const hasNewEvents = events.length > eventCountAtSendRef.current;
    if (hasNewEvents && (taskState !== "idle" || assistantPhase.phase !== "idle")) {
      setIsWaitingForAgent(false);
    }
  }, [isWaitingForAgent, taskState, events.length, assistantPhase.phase]);

  // Update conversation title when the LLM generates one
  useEffect(() => {
    if (!conversationId) return;
    const titleEvent = events.find((e) => e.type === "conversation_title");
    if (titleEvent) {
      const title = titleEvent.data.title as string;
      if (title) {
        updateConversationTitle(conversationId, title);
      }
    }
  }, [conversationId, events, updateConversationTitle]);

  const allMessages = useMemo(() => {
    const combined = [...userMessages, ...assistantMessages];
    return [...combined].sort((a, b) => a.timestamp - b.timestamp);
  }, [userMessages, assistantMessages]);

  const handleCreateConversation = useCallback(
    async (message: string) => {
      eventCountAtSendRef.current = events.length;
      setIsWaitingForAgent(true);
      setUserMessages([
        { role: "user", content: message, timestamp: Date.now() },
      ]);

      try {
        const data = await createConversation(message);
        startConversation(data.conversation_id, message);
      } catch (err) {
        console.error("Failed to create conversation:", err);
        setIsWaitingForAgent(false);
        setUserMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error: ${err instanceof Error ? err.message : "Unknown error"}`,
            timestamp: Date.now(),
          },
        ]);
      }
    },
    [startConversation, events.length],
  );

  const handleSendFollowUp = useCallback(
    async (message: string) => {
      if (!conversationId) return;

      eventCountAtSendRef.current = events.length;
      setIsWaitingForAgent(true);
      setUserMessages((prev) => [
        ...prev,
        { role: "user", content: message, timestamp: Date.now() },
      ]);

      try {
        await sendFollowUpMessage(conversationId, message);
      } catch (err) {
        console.error("Failed to send message:", err);
        setIsWaitingForAgent(false);
        setUserMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error: ${err instanceof Error ? err.message : "Unknown error"}`,
            timestamp: Date.now(),
          },
        ]);
      }
    },
    [conversationId, events.length],
  );

  const handleResumeConversation = useCallback(
    async (message: string) => {
      if (!conversationId) return;

      eventCountAtSendRef.current = events.length;
      setIsWaitingForAgent(true);
      setUserMessages((prev) => [
        ...prev,
        { role: "user", content: message, timestamp: Date.now() },
      ]);

      try {
        await sendFollowUpMessage(conversationId, message);
        resumeConversation();
      } catch (err) {
        console.error("Failed to resume conversation:", err);
        setIsWaitingForAgent(false);
        setUserMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error: ${err instanceof Error ? err.message : "Unknown error"}`,
            timestamp: Date.now(),
          },
        ]);
      }
    },
    [conversationId, resumeConversation, events.length],
  );

  const handleSendMessage = useCallback(
    (message: string) => {
      if (!conversationId) {
        handleCreateConversation(message);
      } else if (!isLiveConversation) {
        handleResumeConversation(message);
      } else {
        handleSendFollowUp(message);
      }
    },
    [conversationId, isLiveConversation, handleCreateConversation, handleResumeConversation, handleSendFollowUp],
  );

  const handleSwitchConversation = useCallback(
    (id: string) => {
      if (id === conversationId) return;
      switchConversation(id);
      setUserMessages([]);
    },
    [conversationId, switchConversation],
  );

  const handleNewConversation = useCallback(() => {
    resetConversation();
    setUserMessages([]);
  }, [resetConversation]);

  return {
    conversationId,
    allMessages,
    isWaitingForAgent,
    handleSendMessage,
    handleCreateConversation,
    handleSwitchConversation,
    handleNewConversation,
  };
}

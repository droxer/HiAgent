"use client";

import { useState, useEffect, useRef } from "react";
import { fetchMessages, fetchEvents } from "../api/history-api";
import type { ChatMessage, AgentEvent } from "@/shared/types";

/**
 * Loads messages and events from the history API for a non-live (historical) conversation.
 * Preserves history when transitioning from historical to live (resume).
 * Only clears when conversationId changes.
 */
export function useConversationHistory(
  conversationId: string | null,
  isLive: boolean,
) {
  const [historyMessages, setHistoryMessages] = useState<ChatMessage[]>([]);
  const [historyEvents, setHistoryEvents] = useState<AgentEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const prevConversationId = useRef<string | null>(null);

  // Clear history only when conversationId changes
  useEffect(() => {
    if (prevConversationId.current !== conversationId) {
      prevConversationId.current = conversationId;
      if (!conversationId) {
        setHistoryMessages([]);
        setHistoryEvents([]);
      }
    }
  }, [conversationId]);

  // Fetch history for non-live conversations
  useEffect(() => {
    if (!conversationId || isLive) {
      return;
    }

    let cancelled = false;
    setIsLoading(true);

    Promise.all([
      fetchMessages(conversationId),
      fetchEvents(conversationId),
    ])
      .then(([messagesResponse, eventsResponse]) => {
        if (cancelled) return;

        const messages: ChatMessage[] = messagesResponse.messages
          .filter((m) => m.role === "user" || m.role === "assistant")
          .map((m) => {
            let text: string;
            if (typeof m.content === "string") {
              text = m.content;
            } else if (
              m.content &&
              typeof m.content === "object" &&
              "text" in m.content
            ) {
              text = String(m.content.text);
            } else {
              text = JSON.stringify(m.content);
            }
            return {
              role: m.role as "user" | "assistant",
              content: text,
              timestamp: new Date(m.created_at).getTime(),
            };
          });

        const events: AgentEvent[] = eventsResponse.events.map((e) => ({
          type: e.type as AgentEvent["type"],
          data: e.data,
          timestamp: new Date(e.timestamp).getTime(),
          iteration: e.iteration,
        }));

        setHistoryMessages(messages);
        setHistoryEvents(events);
      })
      .catch((err) => {
        if (!cancelled) {
          console.error("Failed to load conversation history:", err);
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [conversationId, isLive]);

  return { historyMessages, historyEvents, isLoading };
}

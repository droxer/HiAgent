"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { TopBar } from "@/shared/components/TopBar";
import { MarkdownRenderer } from "@/shared/components/MarkdownRenderer";
import { AgentProgressCard } from "@/features/agent-activity/components/AgentProgressCard";
import { LivePanel } from "@/features/agent-activity/components/LivePanel";
import { TypingIndicator } from "@/features/conversation/components/TypingIndicator";
import { TaskCompleteBanner } from "@/features/conversation/components/TaskCompleteBanner";
import { ChatInput } from "@/features/conversation/components/ChatInput";
import { cn } from "@/shared/lib/utils";
import type {
  AgentEvent,
  TaskState,
  ChatMessage,
  ToolCallInfo,
  AgentStatus,
} from "@/shared/types/events";

interface TaskViewProps {
  events: AgentEvent[];
  messages: ChatMessage[];
  toolCalls: ToolCallInfo[];
  agentStatuses: AgentStatus[];
  taskState: TaskState;
  thinkingContent: string;
  reasoningSteps: string[];
  currentIteration: number;
  isConnected: boolean;
  onSendMessage: (message: string) => void;
  onNavigateHome?: () => void;
}

export function TaskView({
  events,
  messages,
  toolCalls,
  agentStatuses,
  taskState,
  thinkingContent,
  reasoningSteps,
  currentIteration,
  isConnected,
  onSendMessage,
  onNavigateHome,
}: TaskViewProps) {
  const chatScrollRef = useRef<HTMLDivElement>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const autoOpenedRef = useRef(false);

  useEffect(() => {
    chatScrollRef.current?.scrollTo({
      top: chatScrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, events, toolCalls]);

  // Auto-open panel when artifacts appear (tool results with output)
  const hasArtifacts = toolCalls.some((tc) => tc.output !== undefined);
  useEffect(() => {
    if (hasArtifacts && !autoOpenedRef.current) {
      autoOpenedRef.current = true;
      setPanelOpen(true);
    }
  }, [hasArtifacts]);

  const handleProgressCardClick = useCallback(() => {
    setPanelOpen((prev) => !prev);
  }, []);

  const showTyping =
    (taskState === "executing" || taskState === "planning") &&
    messages.length > 0 &&
    messages[messages.length - 1].role === "user";

  return (
    <div className="flex h-screen flex-col">
      <TopBar
        taskState={taskState}
        isConnected={isConnected}
        currentIteration={currentIteration}
        onNavigateHome={onNavigateHome}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Left pane: Conversation */}
        <div className={cn("flex flex-col border-r border-border", panelOpen ? "w-1/2" : "w-full")}>
          <div ref={chatScrollRef} className="flex-1 overflow-y-auto px-6 py-4">
            {messages.length === 0 && (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-muted-foreground">Waiting for response...</p>
              </div>
            )}

            <div className={cn("mx-auto space-y-4", !panelOpen && "max-w-3xl")}>
              {messages.map((msg, i) => (
                <motion.div
                  key={`msg-${i}`}
                  className={cn(msg.role === "user" ? "flex justify-end" : "")}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.15, ease: "easeOut" }}
                >
                  <div
                    className={cn(
                      "max-w-[85%] rounded-lg px-4 py-3 text-sm leading-relaxed",
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-foreground"
                    )}
                  >
                    {msg.role === "assistant" ? (
                      <MarkdownRenderer content={msg.content} />
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>
                </motion.div>
              ))}

              {showTyping && <TypingIndicator />}
            </div>

            {taskState === "complete" && <TaskCompleteBanner />}
          </div>

          {taskState !== "idle" && (
            <div className={cn("border-t border-border px-6 py-3", !panelOpen && "mx-auto w-full max-w-3xl")}>
              <AgentProgressCard
                events={events}
                toolCalls={toolCalls}
                agentStatuses={agentStatuses}
                taskState={taskState}
                thinkingContent={thinkingContent}
                onClick={handleProgressCardClick}
                panelOpen={panelOpen}
              />
            </div>
          )}

          <div className={cn(!panelOpen && "mx-auto w-full max-w-3xl")}>
            <ChatInput onSendMessage={onSendMessage} />
          </div>
        </div>

        {/* Right pane: HiAgent's Computer — only visible when open */}
        {panelOpen && (
          <motion.div
            className="flex w-1/2 flex-col"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
          >
            <LivePanel
              reasoningSteps={reasoningSteps}
              thinkingContent={thinkingContent}
              toolCalls={toolCalls}
              agentStatuses={agentStatuses}
              currentIteration={currentIteration}
              taskState={taskState}
              onClose={() => setPanelOpen(false)}
            />
          </motion.div>
        )}
      </div>
    </div>
  );
}

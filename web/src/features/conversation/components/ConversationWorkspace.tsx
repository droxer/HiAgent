"use client";

import { useRef, useEffect, useState, useCallback, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { TopBar, MarkdownRenderer } from "@/shared/components";
import { AgentProgressCard, AgentComputerPanel } from "@/features/agent-computer";
import { NON_ARTIFACT_TOOLS } from "@/features/agent-computer/lib/tool-constants";
import { ChatInput } from "@/features/conversation";
import { AssistantLoadingSkeleton } from "./AssistantLoadingSkeleton";
import { StreamingCursor } from "./StreamingCursor";
import { cn } from "@/shared/lib/utils";
import type {
  AgentEvent,
  ArtifactInfo,
  AssistantPhase,
  TaskState,
  ChatMessage,
  ToolCallInfo,
  AgentStatus,
} from "@/shared/types";

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

interface ConversationWorkspaceProps {
  conversationId: string | null;
  events: AgentEvent[];
  messages: ChatMessage[];
  toolCalls: ToolCallInfo[];
  agentStatuses: AgentStatus[];
  artifacts: ArtifactInfo[];
  taskState: TaskState;
  thinkingContent: string;
  isStreaming: boolean;
  assistantPhase: AssistantPhase;
  reasoningSteps: string[];
  currentIteration: number;
  isConnected: boolean;
  onSendMessage: (message: string) => void;
  onNavigateHome?: () => void;
  isWaitingForAgent?: boolean;
}

export function ConversationWorkspace({
  conversationId,
  events,
  messages,
  toolCalls,
  agentStatuses,
  artifacts,
  taskState,
  thinkingContent,
  isStreaming,
  assistantPhase,
  reasoningSteps,
  currentIteration,
  isConnected,
  onSendMessage,
  onNavigateHome,
  isWaitingForAgent = false,
}: ConversationWorkspaceProps) {
  const chatScrollRef = useRef<HTMLDivElement>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const autoOpenedRef = useRef(false);

  useEffect(() => {
    chatScrollRef.current?.scrollTo({
      top: chatScrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, events, toolCalls]);

  // Collect artifact image URLs from tool calls that have artifact IDs
  const inlineImageUrls = useMemo(() => {
    if (!conversationId) return [];
    return toolCalls
      .filter((tc) => tc.artifactIds && tc.artifactIds.length > 0)
      .flatMap((tc) =>
        tc.artifactIds!.map((aid) => `/api/conversations/${conversationId}/artifacts/${aid}`)
      );
  }, [toolCalls, conversationId]);

  // Auto-open panel when real artifacts appear (sandbox tool results, not web_search etc.)
  const hasArtifacts = useMemo(
    () => toolCalls.some((tc) => tc.output !== undefined && !NON_ARTIFACT_TOOLS.has(tc.name)),
    [toolCalls],
  );
  useEffect(() => {
    if (hasArtifacts && !autoOpenedRef.current) {
      autoOpenedRef.current = true;
      setPanelOpen(true);
    }
  }, [hasArtifacts]);

  const handleProgressCardClick = useCallback(() => {
    setPanelOpen((prev) => !prev);
  }, []);

  const showLoadingSkeleton =
    (isWaitingForAgent || (assistantPhase.phase !== "idle" && !isStreaming)) &&
    messages.length > 0;

  const effectivePhase: AssistantPhase = isWaitingForAgent && assistantPhase.phase === "idle"
    ? { phase: "thinking" }
    : assistantPhase;

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
        <div className={cn("flex flex-col", panelOpen ? "w-1/2 border-r border-border" : "w-full")}>
          <div ref={chatScrollRef} className="flex-1 overflow-y-auto px-6 py-5">
            {messages.length === 0 && (
              <div className="flex h-full items-center justify-center">
                <p className="text-sm text-muted-foreground">Waiting for response...</p>
              </div>
            )}

            <div className={cn("mx-auto space-y-5", !panelOpen && "max-w-3xl")}>
              {messages.map((msg, i) => (
                <motion.div
                  key={`msg-${i}`}
                  className={cn(msg.role === "user" ? "flex justify-end" : "")}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.15, ease: "easeOut" }}
                >
                  {msg.role === "user" ? (
                    <div className={cn("max-w-[80%]", msg.content.length < 60 && "max-w-fit")}>
                      <motion.div
                        className="rounded-2xl rounded-br-md border border-border-strong bg-secondary px-4 py-3.5 text-sm font-medium leading-relaxed tracking-[-0.01em] text-foreground"
                        style={{
                          boxShadow: "0 1px 3px rgba(28,25,23,0.04), 0 1px 2px rgba(28,25,23,0.02)",
                        }}
                        whileHover={{
                          boxShadow: "0 4px 12px rgba(28,25,23,0.06), 0 1px 3px rgba(28,25,23,0.04)",
                        }}
                        transition={{ duration: 0.2 }}
                      >
                        <p className="whitespace-pre-wrap">
                          {msg.content}
                          {msg.timestamp && (
                            <span className="ml-3 inline-block align-baseline text-[10px] font-normal tracking-normal text-muted-foreground/50 tabular-nums select-none">
                              {formatTime(msg.timestamp)}
                            </span>
                          )}
                        </p>
                      </motion.div>
                    </div>
                  ) : (
                    <div className="text-sm leading-relaxed text-foreground">
                      <MarkdownRenderer content={msg.content} />
                      <AnimatePresence>
                        {isStreaming && i === messages.length - 1 && (
                          <StreamingCursor />
                        )}
                      </AnimatePresence>
                      {/* Render generated images inline after the last assistant message */}
                      {i === messages.length - 1 && inlineImageUrls.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-3">
                          {inlineImageUrls.map((url) => (
                            /* eslint-disable-next-line @next/next/no-img-element */
                            <img
                              key={url}
                              src={url}
                              alt="Generated image"
                              className="max-h-72 rounded-lg border border-border object-contain shadow-sm"
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              ))}

              <AnimatePresence mode="wait">
                {showLoadingSkeleton && (
                  <AssistantLoadingSkeleton phase={effectivePhase} />
                )}
              </AnimatePresence>
            </div>

          </div>

          {events.length > 0 && (
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

          <div className={cn("mx-auto w-full", !panelOpen && "max-w-3xl")}>
            <ChatInput
              onSendMessage={onSendMessage}
              disabled={isWaitingForAgent || taskState === "executing"}
            />
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
            <AgentComputerPanel
              conversationId={conversationId}
              thinkingContent={thinkingContent}
              toolCalls={toolCalls}
              agentStatuses={agentStatuses}
              artifacts={artifacts}
              taskState={taskState}
              onClose={() => setPanelOpen(false)}
            />
          </motion.div>
        )}
      </div>
    </div>
  );
}

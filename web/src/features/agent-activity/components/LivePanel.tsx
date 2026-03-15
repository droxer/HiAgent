"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
  Monitor,
  CircleCheck,
  Loader2,
  Lightbulb,
  X,
} from "lucide-react";
import { Badge } from "@/shared/components/ui/badge";
import { formatInput, formatToolPreview } from "@/features/agent-activity/lib/format-tools";
import { AgentStatusRow } from "@/features/agent-activity/components/AgentStatusRow";
import type { ToolCallInfo, AgentStatus, TaskState } from "@/shared/types/events";

interface LivePanelProps {
  reasoningSteps: string[];
  thinkingContent: string;
  toolCalls: ToolCallInfo[];
  agentStatuses: AgentStatus[];
  currentIteration: number;
  taskState: TaskState;
  onClose?: () => void;
}

export function LivePanel({
  thinkingContent,
  toolCalls,
  agentStatuses,
  taskState,
  onClose,
}: LivePanelProps) {
  const terminalRef = useRef<HTMLDivElement>(null);

  // Auto-scroll terminal
  useEffect(() => {
    terminalRef.current?.scrollTo({
      top: terminalRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [toolCalls, thinkingContent]);

  const latestToolCall = toolCalls[toolCalls.length - 1];
  const isRunning = taskState === "executing" || taskState === "planning";

  return (
    <div className="flex h-full flex-col bg-surface-tertiary">
      {/* Header: HiAgent's Computer */}
      <div className="flex shrink-0 items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <Monitor className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-semibold text-foreground">
            HiAgent&apos;s Computer
          </span>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Activity indicator */}
      {isRunning && latestToolCall && (
        <div className="flex shrink-0 items-center gap-2 border-b border-border bg-card px-4 py-2">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-amber-600" />
          <span className="text-xs text-muted-foreground">
            HiAgent is using{" "}
            <span className="font-medium text-foreground">{latestToolCall.name}</span>
          </span>
          {latestToolCall.output === undefined && (
            <span className="ml-auto truncate max-w-[200px] text-xs text-muted-foreground font-mono">
              {formatToolPreview(latestToolCall.input)}
            </span>
          )}
        </div>
      )}

      {/* Terminal content */}
      <div
        ref={terminalRef}
        className="flex-1 overflow-y-auto bg-muted p-4 font-mono text-xs leading-6"
      >
        {toolCalls.length === 0 && !thinkingContent && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
            <Monitor className="h-8 w-8 opacity-30" />
            <p className="text-xs font-sans">Waiting for agent activity...</p>
          </div>
        )}

        {/* Inline reasoning when present */}
        {thinkingContent && (
          <div className="mb-4 rounded-sm border border-purple-500/20 bg-purple-500/5 p-3">
            <div className="mb-1.5 flex items-center gap-2">
              <Lightbulb className="h-3 w-3 text-purple-400" />
              <span className="text-micro font-semibold uppercase tracking-wider text-purple-400 font-sans">
                Thinking
              </span>
              <Loader2 className="h-3 w-3 animate-spin text-purple-400" />
            </div>
            <p className="whitespace-pre-wrap text-muted-foreground font-sans text-xs leading-relaxed">
              {thinkingContent}
            </p>
          </div>
        )}

        {/* Tool calls as terminal output */}
        {toolCalls.map((tc) => (
          <motion.div
            key={tc.id}
            className="mb-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.15 }}
          >
            {/* Command line */}
            <div className="flex items-start gap-2">
              <div className="flex flex-1 items-center gap-2">
                <span className="font-semibold text-foreground">{tc.name}</span>
                {Object.keys(tc.input).length > 0 && (
                  <span className="text-muted-foreground">{formatInput(tc.input)}</span>
                )}
              </div>
              {tc.output !== undefined ? (
                <CircleCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" />
              ) : (
                <Loader2 className="mt-0.5 h-3.5 w-3.5 shrink-0 animate-spin text-amber-600" />
              )}
            </div>

            {/* Output */}
            {tc.output !== undefined && (
              <div className="ml-0 mt-1 whitespace-pre-wrap text-muted-foreground border-l-2 border-border pl-3 py-1">
                {tc.output.length > 500 ? tc.output.slice(0, 500) + "\n..." : tc.output}
              </div>
            )}

            {tc.output === undefined && (
              <div className="ml-4 mt-1 text-muted-foreground animate-pulse">
                Running...
              </div>
            )}
          </motion.div>
        ))}

        {/* Agents inline */}
        {agentStatuses.length > 0 && (
          <div className="mt-3 space-y-2">
            {agentStatuses.map((agent) => (
              <AgentStatusRow key={agent.agentId} agent={agent} />
            ))}
          </div>
        )}
      </div>

      {/* Bottom: Timeline scrubber */}
      <div className="flex shrink-0 items-center gap-3 border-t border-border bg-card px-4 py-2">
        {/* Progress bar */}
        <div className="flex-1">
          <div className="h-1 w-full rounded-sm bg-border">
            <div
              className="h-1 rounded-sm bg-amber-500 transition-all duration-500"
              style={{
                width: taskState === "complete"
                  ? "100%"
                  : taskState === "idle"
                    ? "0%"
                    : `${Math.min(90, (toolCalls.filter((t) => t.output !== undefined).length / Math.max(1, toolCalls.length)) * 100)}%`,
              }}
            />
          </div>
        </div>

        {/* Live indicator */}
        {isRunning && (
          <div className="flex items-center gap-2">
            <div className="h-[6px] w-[6px] rounded-full bg-emerald-500" />
            <span className="text-micro font-semibold uppercase tracking-widest text-emerald-600 font-sans">
              LIVE
            </span>
          </div>
        )}

        {taskState === "complete" && (
          <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-500 text-micro">
            Done
          </Badge>
        )}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef, useMemo, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Monitor,
  CircleCheck,
  CircleX,
  X,
  FolderOpen,
} from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Progress } from "@/shared/components/ui/progress";
import { formatInput, formatToolPreview } from "../lib/format-tools";
import { HIDDEN_ACTIVITY_TOOLS, normalizeToolName } from "../lib/tool-constants";
import { normalizeSkillName } from "@/features/skills/lib/normalize-skill-name";
import { ToolOutputRenderer } from "./ToolOutputRenderer";
import { SkillActivityEntry } from "./SkillActivityEntry";
import { AgentStatusRow } from "./AgentStatusRow";
import { ArtifactFilesPanel } from "./ArtifactFilesPanel";
import { cn } from "@/shared/lib/utils";
import { useTranslation } from "@/i18n";
import { PulsingDot } from "@/shared/components/PulsingDot";
import type { ToolCallInfo, AgentStatus, TaskState, ArtifactInfo } from "@/shared/types";

const SKILL_TOOL_NAMES = new Set(["activate_skill", "load_skill"]);

type TFn = (key: string, params?: Record<string, string | number>) => string;

function getToolVerb(name: string, t: TFn): string {
  const key = `tools.verb.${name}`;
  const translated = t(key);
  // If key returns itself, fall back to generic
  if (translated === key) return t("computer.usingToolGeneric", { name: normalizeToolName(name) });
  return translated;
}

/* ── status symbol for terminal-style logs ── */
function statusSymbol(tc: ToolCallInfo): string {
  if (tc.output !== undefined) {
    return tc.success === false ? "✗" : "✓";
  }
  return "⟳";
}

function statusColor(tc: ToolCallInfo): string {
  if (tc.output !== undefined) {
    return tc.success === false ? "text-accent-rose" : "text-accent-emerald";
  }
  return "text-ai-glow";
}

type PanelTab = "activity" | "files";

interface AgentComputerPanelProps {
  conversationId: string | null;
  toolCalls: ToolCallInfo[];
  agentStatuses: AgentStatus[];
  artifacts: ArtifactInfo[];
  taskState: TaskState;
  onClose?: () => void;
}

export function AgentComputerPanel({
  conversationId,
  toolCalls,
  agentStatuses,
  artifacts,
  taskState,
  onClose,
}: AgentComputerPanelProps) {
  const { t } = useTranslation();
  const contentRef = useRef<HTMLDivElement>(null);
  const [activeTab, setActiveTab] = useState<PanelTab>("activity");
  const tabListRef = useRef<HTMLDivElement>(null);

  const TABS: PanelTab[] = ["activity", "files"];

  const handleTabKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      e.preventDefault();

      const currentIndex = TABS.indexOf(activeTab);
      const nextIndex =
        e.key === "ArrowRight"
          ? (currentIndex + 1) % TABS.length
          : (currentIndex - 1 + TABS.length) % TABS.length;

      const nextTab = TABS[nextIndex];
      setActiveTab(nextTab);

      const nextButton = tabListRef.current?.querySelector<HTMLElement>(
        `#tab-${nextTab}`,
      );
      nextButton?.focus();
    },
    [activeTab],
  );

  const visibleToolCalls = useMemo(
    () => toolCalls.filter((t) => !HIDDEN_ACTIVITY_TOOLS.has(t.name)),
    [toolCalls],
  );

  useEffect(() => {
    contentRef.current?.scrollTo({
      top: contentRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [visibleToolCalls]);
  const latestToolCall = visibleToolCalls[visibleToolCalls.length - 1];
  const isRunning = taskState === "executing" || taskState === "planning";

  const completedCount = useMemo(
    () => visibleToolCalls.filter((t) => t.output !== undefined).length,
    [visibleToolCalls],
  );

  const progressValue = useMemo(() => {
    if (taskState === "complete") return 100;
    if (taskState === "idle" || visibleToolCalls.length === 0) return 0;
    return Math.min(95, (completedCount / Math.max(1, visibleToolCalls.length)) * 100);
  }, [taskState, visibleToolCalls.length, completedCount]);

  return (
    <div className="flex h-full flex-col bg-background">
      {/* ── Header with tabs ── */}
      <div className="shrink-0 border-b border-border">
        <div className="flex items-center justify-between px-4 pt-3 pb-0">
          <span className="text-sm font-semibold tracking-tight text-foreground">
            {t("computer.title")}
          </span>
          <div className="flex items-center gap-1">
            {onClose && (
              <Button
                type="button"
                variant="ghost"
                size="icon-xs"
                aria-label={t("computer.closePanel")}
                onClick={onClose}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
        <div ref={tabListRef} className="flex gap-1 px-3 pt-2 sm:px-4" role="tablist" aria-label={t("computer.tabsLabel")} onKeyDown={handleTabKeyDown}>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "activity"}
            aria-controls="panel-activity"
            id="tab-activity"
            tabIndex={activeTab === "activity" ? 0 : -1}
            onClick={() => setActiveTab("activity")}
            className={cn(
              "flex items-center gap-1.5 rounded-t-md px-3 py-1.5 text-xs font-medium transition-colors",
              activeTab === "activity"
                ? "border-b-2 border-foreground text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <Monitor className="h-3 w-3" />
            {t("computer.activity")}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "files"}
            aria-controls="panel-files"
            id="tab-files"
            tabIndex={activeTab === "files" ? 0 : -1}
            onClick={() => setActiveTab("files")}
            className={cn(
              "flex items-center gap-1.5 rounded-t-md px-3 py-1.5 text-xs font-medium transition-colors",
              activeTab === "files"
                ? "border-b-2 border-foreground text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <FolderOpen className="h-3 w-3" />
            {t("computer.artifacts")}
            {artifacts.length > 0 && (
              <span className="ml-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-muted px-1 text-[0.625rem] font-semibold">
                {artifacts.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* ── Files tab ── */}
      {activeTab === "files" && (
        <div id="panel-files" role="tabpanel" aria-labelledby="tab-files" className="flex-1 overflow-y-auto">
          <ArtifactFilesPanel artifacts={artifacts} conversationId={conversationId} />
        </div>
      )}

      {/* ── Activity tab ── */}
      {activeTab === "activity" && isRunning && latestToolCall && (
        <div className="flex shrink-0 items-center gap-2 border-b border-border bg-secondary/50 px-4 py-2" role="status" aria-live="polite">
          <PulsingDot size="sm" />
          <span className="text-xs text-muted-foreground">
            {SKILL_TOOL_NAMES.has(latestToolCall.name)
              ? t("computer.loadingSkill", { name: normalizeSkillName(String(latestToolCall.input.name ?? "skill")) })
              : t("computer.usingTool", { verb: getToolVerb(latestToolCall.name, t) })}
          </span>
          {latestToolCall.output === undefined && !SKILL_TOOL_NAMES.has(latestToolCall.name) && (
            <span className="ml-auto max-w-[240px] truncate font-mono text-xs text-muted-foreground-dim">
              {formatToolPreview(latestToolCall.input)}
            </span>
          )}
        </div>
      )}

      {/* ── Activity content area — terminal-style logs ── */}
      {activeTab === "activity" && (
        <div id="panel-activity" role="tabpanel" aria-labelledby="tab-activity" className="flex min-h-0 flex-1 flex-col">
          <div
            ref={contentRef}
            className="flex-1 overflow-y-auto px-3 py-4 sm:px-6"
          >
            {/* Empty state */}
            {visibleToolCalls.length === 0 && (
              <div className="flex h-full flex-col items-center justify-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-md bg-secondary">
                  <Monitor className="h-5 w-5 text-muted-foreground-dim" />
                </div>
                <p className="text-xs text-muted-foreground">
                  {t("computer.waitingActivity")}
                </p>
              </div>
            )}

            {/* Terminal-style tool call entries */}
            <div className="space-y-1 font-mono text-xs">
              {visibleToolCalls.map((tc) =>
                SKILL_TOOL_NAMES.has(tc.name) ? (
                  <SkillActivityEntry key={tc.id} toolCall={tc} />
                ) : (
                  <motion.div
                    key={tc.id}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.15, ease: "easeOut" }}
                  >
                    {/* Log line */}
                    <div className="flex items-start gap-2 py-1">
                      <span className={cn("shrink-0", statusColor(tc))}>
                        [{statusSymbol(tc)}]
                      </span>
                      <span className="text-foreground">
                        {normalizeToolName(tc.name)}
                      </span>
                      {Object.keys(tc.input).length > 0 && (
                        <span className="text-muted-foreground-dim">
                          — {formatInput(tc.input)}
                        </span>
                      )}
                      {tc.output === undefined && (
                        <motion.span
                          className="text-ai-glow"
                          animate={{ opacity: [0.3, 1, 0.3] }}
                          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                        >
                          {t("computer.running")}
                        </motion.span>
                      )}
                    </div>

                    {/* Output (collapsible) */}
                    {tc.output !== undefined && (
                      <div className="ml-6 mb-2">
                        <ToolOutputRenderer
                          output={tc.output}
                          toolName={tc.name}
                          contentType={tc.contentType}
                          conversationId={conversationId}
                          artifactIds={tc.artifactIds}
                        />
                      </div>
                    )}
                  </motion.div>
                ),
              )}
            </div>

            {/* Agent statuses */}
            {agentStatuses.length > 0 && (
              <div className="mt-4 space-y-2">
                {agentStatuses.map((agent) => (
                  <AgentStatusRow key={agent.agentId} agent={agent} variant="light" />
                ))}
              </div>
            )}
          </div>

          {/* ── Consolidated status bar ── */}
          <div className="flex shrink-0 items-center gap-3 border-t border-border px-4 py-2.5">
            <Progress value={progressValue} className="flex-1 h-1.5" />

            <div className="flex items-center gap-1.5">
              {isRunning ? (
                <PulsingDot size="sm" />
              ) : taskState === "complete" ? (
                <CircleCheck className="h-3.5 w-3.5 text-accent-emerald" />
              ) : taskState === "error" ? (
                <CircleX className="h-3.5 w-3.5 text-accent-rose" />
              ) : null}
              <span className="text-xs font-medium text-muted-foreground">
                {taskState === "complete"
                  ? t("computer.statusDone")
                  : isRunning
                    ? t("computer.statusLive")
                    : taskState === "error"
                      ? t("computer.statusError")
                      : t("computer.statusIdle")}
              </span>
            </div>

            <span className="text-xs font-mono font-medium text-muted-foreground tabular-nums">
              {completedCount}/{visibleToolCalls.length}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

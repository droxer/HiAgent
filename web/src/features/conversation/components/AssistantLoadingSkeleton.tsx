"use client";

import { motion } from "framer-motion";
import type { AssistantPhase } from "@/shared/types";
import { normalizeToolName } from "@/features/agent-computer/lib/tool-constants";

interface AssistantLoadingSkeletonProps {
  readonly phase: AssistantPhase;
}

function getPhaseLabel(phase: AssistantPhase): string {
  switch (phase.phase) {
    case "thinking":
      return "Thinking...";
    case "writing":
      return "Writing...";
    case "using_tool":
      return `Using ${normalizeToolName(phase.toolName ?? "tool")}...`;
    default:
      return "";
  }
}

export function AssistantLoadingSkeleton({ phase }: AssistantLoadingSkeletonProps) {
  if (phase.phase === "idle") return null;

  const label = getPhaseLabel(phase);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4, transition: { duration: 0.15 } }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      {/* AI indicator row */}
      <div className="mb-2 flex items-center gap-2">
        <div className="relative">
          <motion.div
            className="h-2 w-2 rounded-full bg-ai-glow"
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          />
          <span
            className="absolute inset-0 rounded-full bg-ai-glow"
            style={{ animation: "orbitalPulse 2s ease-out infinite" }}
          />
        </div>
        <span className="text-xs font-medium tracking-wide text-ai-glow/70 uppercase">
          HiAgent
        </span>
      </div>

      {/* Shimmer skeleton + phase label */}
      <div className="pl-[18px] space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-sm text-ai-glow/70">{label}</span>
        </div>
        <div className="flex flex-col gap-1.5">
          <div
            className="h-3 w-48 rounded-full bg-secondary"
            style={{
              backgroundImage: "linear-gradient(90deg, var(--color-secondary) 0%, var(--color-border) 50%, var(--color-secondary) 100%)",
              backgroundSize: "200% 100%",
              animation: "shimmer 2s linear infinite",
            }}
          />
          <div
            className="h-3 w-32 rounded-full bg-secondary"
            style={{
              backgroundImage: "linear-gradient(90deg, var(--color-secondary) 0%, var(--color-border) 50%, var(--color-secondary) 100%)",
              backgroundSize: "200% 100%",
              animation: "shimmer 2s linear infinite 0.15s",
            }}
          />
        </div>
      </div>
    </motion.div>
  );
}

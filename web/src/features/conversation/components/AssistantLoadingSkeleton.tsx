"use client";

import { motion } from "framer-motion";
import type { AssistantPhase } from "@/shared/types";
import { Brain, Wrench, Pencil } from "lucide-react";

interface AssistantLoadingSkeletonProps {
  readonly phase: AssistantPhase;
}

const PHASE_META: Record<
  Exclude<AssistantPhase["phase"], "idle">,
  { icon: typeof Brain; label: string; accent: string }
> = {
  thinking: {
    icon: Brain,
    label: "Thinking",
    accent: "text-accent-amber",
  },
  writing: {
    icon: Pencil,
    label: "Writing",
    accent: "text-accent-blue",
  },
  using_tool: {
    icon: Wrench,
    label: "Using tool",
    accent: "text-accent-purple",
  },
};

function PulsingDots() {
  return (
    <div className="flex items-center gap-1 pt-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40"
          animate={{
            scale: [1, 1.4, 1],
            opacity: [0.3, 0.8, 0.3],
          }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 0.2,
          }}
        />
      ))}
    </div>
  );
}

export function AssistantLoadingSkeleton({ phase }: AssistantLoadingSkeletonProps) {
  if (phase.phase === "idle") return null;

  const meta = PHASE_META[phase.phase];
  const Icon = meta.icon;
  const label =
    phase.phase === "using_tool" ? `Using ${phase.toolName}` : meta.label;

  return (
    <motion.div
      className="flex items-start gap-3"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4, transition: { duration: 0.15 } }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      {/* Phase badge */}
      <motion.div
        className={`mt-0.5 flex items-center gap-1.5 ${meta.accent}`}
        animate={{ opacity: [0.6, 1, 0.6] }}
        transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
      >
        <Icon className="h-4 w-4" />
      </motion.div>

      {/* Skeleton content area */}
      <div className="flex-1 space-y-3">
        {/* Phase label */}
        <motion.span
          className="text-xs font-medium tracking-wide text-muted-foreground"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2, delay: 0.1 }}
        >
          {label}
          <motion.span
            animate={{ opacity: [0, 1, 0] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          >
            ...
          </motion.span>
        </motion.span>

        <PulsingDots />
      </div>
    </motion.div>
  );
}

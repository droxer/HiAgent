"use client";

import { motion } from "framer-motion";
import { CircleCheck, GitFork, CircleX } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import type { AgentStatus } from "@/shared/types";

interface AgentStatusRowProps {
  readonly agent: AgentStatus;
  readonly variant?: "light" | "dark";
}

export function AgentStatusRow({ agent, variant = "light" }: AgentStatusRowProps) {
  const isDark = variant === "dark";

  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md px-2.5 py-1.5 text-xs",
        isDark ? "bg-white/5" : "bg-secondary",
      )}
    >
      {agent.status === "complete" ? (
        <CircleCheck className="h-3.5 w-3.5 shrink-0 text-accent-emerald" />
      ) : agent.status === "error" ? (
        <CircleX className="h-3.5 w-3.5 shrink-0 text-accent-rose" />
      ) : (
        <motion.span
          className="h-2 w-2 shrink-0 rounded-full bg-ai-glow"
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
        />
      )}
      <GitFork className={cn("h-3 w-3 shrink-0", isDark ? "text-terminal-dim" : "text-muted-foreground-dim")} />
      <span className={cn("flex-1 truncate", isDark ? "text-[var(--color-terminal-text)]" : "text-foreground")}>
        {agent.description}
      </span>
      <span className={cn("ml-auto font-mono text-micro", isDark ? "text-[var(--color-terminal-dim)]" : "text-muted-foreground")}>
        {agent.agentId.slice(0, 8)}
      </span>
    </div>
  );
}

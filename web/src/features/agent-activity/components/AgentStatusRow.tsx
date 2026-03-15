"use client";

import {
  Loader2,
  CircleCheck,
  CircleAlert,
  GitFork,
} from "lucide-react";
import type { AgentStatus } from "@/shared/types/events";

interface AgentStatusRowProps {
  readonly agent: AgentStatus;
}

export function AgentStatusRow({ agent }: AgentStatusRowProps) {
  return (
    <div className="flex items-center gap-2 rounded-sm bg-muted px-3 py-2">
      {agent.status === "running" ? (
        <Loader2 className="h-3 w-3 animate-spin text-amber-600" />
      ) : agent.status === "complete" ? (
        <CircleCheck className="h-3 w-3 text-emerald-600" />
      ) : (
        <CircleAlert className="h-3 w-3 text-rose-500" />
      )}
      <GitFork className="h-3 w-3 text-muted-foreground" />
      <span className="font-sans text-xs text-foreground">{agent.description}</span>
      <span className="ml-auto font-mono text-micro text-muted-foreground">
        {agent.agentId.slice(0, 8)}
      </span>
    </div>
  );
}

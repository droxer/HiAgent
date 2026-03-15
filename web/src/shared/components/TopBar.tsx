"use client";

import { LayoutGrid } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import type { TaskState } from "@/shared/types/events";

interface TopBarProps {
  taskState: TaskState;
  isConnected: boolean;
  currentIteration: number;
  onNavigateHome?: () => void;
}

export function TopBar({ taskState, isConnected, currentIteration, onNavigateHome }: TopBarProps) {
  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b border-border bg-card px-4">
      {/* Left: Breadcrumb */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onNavigateHome}
          className="gap-2 text-muted-foreground hover:text-foreground"
        >
          <LayoutGrid className="h-4 w-4" />
          HiAgent
        </Button>
        {taskState !== "idle" && (
          <>
            <span className="text-muted-foreground">/</span>
            <span className="text-sm text-muted-foreground">
              Task {currentIteration > 0 ? `(Step ${currentIteration})` : ""}
            </span>
          </>
        )}
        {isConnected && (
          <span className="ml-2 h-1.5 w-1.5 rounded-full bg-emerald-500" />
        )}
      </div>

    </header>
  );
}

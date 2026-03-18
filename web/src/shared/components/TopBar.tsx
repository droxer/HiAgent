"use client";

import { useCallback } from "react";
import { LayoutGrid, Search } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { useTranslation } from "@/i18n";
import type { TaskState } from "@/shared/types";

interface TopBarProps {
  taskState: TaskState;
  isConnected: boolean;
  currentIteration: number;
  onNavigateHome?: () => void;
  taskTitle?: string;
}

export function TopBar({
  taskState,
  isConnected,
  currentIteration,
  onNavigateHome,
  taskTitle,
}: TopBarProps) {
  const { t } = useTranslation();

  const handleOpenCommandPalette = useCallback(() => {
    // Dispatch the same Cmd+K event the CommandPalette listens for
    document.dispatchEvent(
      new KeyboardEvent("keydown", { key: "k", metaKey: true, bubbles: true }),
    );
  }, []);

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-background px-4">
      {/* Left: Breadcrumb */}
      <div className="flex items-center gap-1.5">
        <Button
          variant="ghost"
          size="sm"
          onClick={onNavigateHome}
          className="gap-2 text-muted-foreground hover:text-foreground"
        >
          <LayoutGrid className="h-3.5 w-3.5" />
          {t("topbar.brand")}
        </Button>
        {taskState !== "idle" && (
          <>
            <span className="text-xs text-muted-foreground-dim">/</span>
            <span className="text-xs text-muted-foreground">
              {taskTitle ?? (currentIteration > 0 ? t("topbar.taskStep", { step: currentIteration }) : t("topbar.task"))}
            </span>
          </>
        )}
        {isConnected && (
          <span className="ml-1.5 h-2 w-2 rounded-full bg-accent-emerald" aria-label={t("topbar.connected")} title={t("topbar.connected")} />
        )}
      </div>

      {/* Right: Command palette trigger */}
      <button
        type="button"
        onClick={handleOpenCommandPalette}
        className="flex items-center gap-2 rounded-md border border-border bg-secondary/50 px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
      >
        <Search className="h-3 w-3" />
        <span>{t("topbar.search")}</span>
        <kbd className="font-mono text-micro text-muted-foreground-dim">⌘K</kbd>
      </button>
    </header>
  );
}

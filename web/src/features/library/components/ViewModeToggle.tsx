"use client";

import { LayoutList, LayoutGrid } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { useTranslation } from "@/i18n";
import type { ViewMode } from "../types";

interface ViewModeToggleProps {
  readonly viewMode: ViewMode;
  readonly onViewModeChange: (mode: ViewMode) => void;
}

export function ViewModeToggle({
  viewMode,
  onViewModeChange,
}: ViewModeToggleProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center rounded-lg border border-border bg-secondary/50 p-0.5">
      <button
        type="button"
        onClick={() => onViewModeChange("list")}
        aria-label={t("library.viewList")}
        aria-pressed={viewMode === "list"}
        className={cn(
          "flex h-7 w-7 items-center justify-center rounded-md transition-colors duration-150",
          viewMode === "list"
            ? "bg-card text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground",
        )}
      >
        <LayoutList className="h-3.5 w-3.5" />
      </button>
      <button
        type="button"
        onClick={() => onViewModeChange("grid")}
        aria-label={t("library.viewGrid")}
        aria-pressed={viewMode === "grid"}
        className={cn(
          "flex h-7 w-7 items-center justify-center rounded-md transition-colors duration-150",
          viewMode === "grid"
            ? "bg-card text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground",
        )}
      >
        <LayoutGrid className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

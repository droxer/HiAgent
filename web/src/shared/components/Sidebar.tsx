"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { Plus, PanelLeftClose, PanelLeftOpen, Search, X, Trash2, Blocks } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { ScrollArea } from "@/shared/components/ui/scroll-area";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/shared/components/ui/tooltip";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/components/ui/alert-dialog";
import { cn } from "@/shared/lib/utils";
import type { ConversationHistoryItem } from "@/shared/stores";

interface SidebarProps {
  taskHistory: readonly ConversationHistoryItem[];
  activeTaskId?: string | null;
  onNewTask: () => void;
  onSelectTask?: (taskId: string) => void;
  collapsed?: boolean;
  width?: number;
  onToggle?: () => void;
  onWidthChange?: (width: number) => void;
  onLoadMore?: () => void;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  onDeleteTask?: (taskId: string) => void;
}


export function Sidebar({
  taskHistory,
  activeTaskId,
  onNewTask,
  onSelectTask,
  collapsed = false,
  width = 256,
  onToggle,
  onWidthChange,
  onLoadMore,
  searchQuery = "",
  onSearchChange,
  onDeleteTask,
}: SidebarProps) {
  const [taskToDelete, setTaskToDelete] = useState<ConversationHistoryItem | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragStartX = useRef(0);
  const dragStartWidth = useRef(0);

  const handleDragStart = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsDragging(true);
      dragStartX.current = e.clientX;
      dragStartWidth.current = width;
    },
    [width],
  );

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      const delta = e.clientX - dragStartX.current;
      onWidthChange?.(dragStartWidth.current + delta);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, onWidthChange]);

  const handleConfirmDelete = () => {
    if (taskToDelete && onDeleteTask) {
      onDeleteTask(taskToDelete.id);
    }
    setTaskToDelete(null);
  };

  return (
    <aside
      className={cn(
        "relative flex h-screen shrink-0 flex-col overflow-hidden",
        collapsed ? "w-12" : "",
        !collapsed && !isDragging && "transition-[width] duration-200 ease-in-out",
      )}
      style={collapsed ? undefined : { width }}
    >
      {/* Subtle gradient background matching main panel aesthetic */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background: [
            "linear-gradient(180deg, var(--color-background) 0%, var(--color-sidebar-bg) 30%, var(--color-background) 100%)",
            "radial-gradient(ellipse 80% 50% at 50% 0%, var(--color-ai-surface) 0%, transparent 70%)",
          ].join(", "),
        }}
      />

      {/* Right edge separator — soft shadow instead of hard border */}
      <div className="pointer-events-none absolute right-0 top-0 h-full w-px bg-border/60" />

      {/* Header: logo + collapse/expand toggle */}
      <div className={cn("relative flex items-center py-4", collapsed ? "flex-col gap-2 px-2" : "justify-between px-4")}>
        <div className="flex items-center gap-2.5">
          <Image
            src="/logo.png"
            alt="HiAgent logo"
            width={28}
            height={28}
            className="rounded-md shrink-0"
          />
          {!collapsed && (
            <span className="text-sm font-semibold tracking-tight text-foreground whitespace-nowrap">
              HiAgent
            </span>
          )}
        </div>
        {onToggle && (
          collapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon-sm" onClick={onToggle} className="text-muted-foreground hover:text-foreground hover:bg-sidebar-hover">
                  <PanelLeftOpen className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">Expand sidebar</TooltipContent>
            </Tooltip>
          ) : (
            <Button variant="ghost" size="icon-sm" onClick={onToggle} className="text-muted-foreground hover:text-foreground hover:bg-sidebar-hover focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50">
              <PanelLeftClose className="h-4 w-4" />
            </Button>
          )
        )}
      </div>

      {/* New task button */}
      <div className={cn("relative", collapsed ? "px-2 pb-2" : "px-3 pb-3")}>
        {collapsed ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                onClick={onNewTask}
                variant="ghost"
                className="w-full border border-border/50 hover:border-border-active hover:bg-card/80 backdrop-blur-sm transition-all duration-200"
                size="icon"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">New task</TooltipContent>
          </Tooltip>
        ) : (
          <Button
            onClick={onNewTask}
            variant="outline"
            className="w-full justify-start gap-2 rounded-xl border-border/50 bg-card/60 backdrop-blur-sm hover:border-border-active hover:bg-card/80 hover:shadow-card"
          >
            <Plus className="h-4 w-4 text-muted-foreground" />
            New task
          </Button>
        )}
      </div>

      {/* Search input (expanded mode only) */}
      {!collapsed && onSearchChange && (
        <div className="relative px-3 pb-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground/70" />
            <input
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="h-8 w-full rounded-lg border border-border/50 bg-card/40 pl-8 pr-8 text-sm text-foreground placeholder:text-placeholder backdrop-blur-sm outline-none transition-all duration-200 focus:border-border-active focus:bg-card/70 focus:shadow-[0_0_12px_var(--color-input-glow)]"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => onSearchChange("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Task list */}
      <div className={cn("relative min-h-0 flex-1", collapsed ? "px-2" : "px-2")}>
        <ScrollArea
          className="h-full"
          onScrollCapture={(e: React.UIEvent<HTMLDivElement>) => {
            if (!onLoadMore) return;
            const target = e.currentTarget;
            const scrollEl = target.querySelector("[data-radix-scroll-area-viewport]");
            if (!scrollEl) return;
            const { scrollTop, scrollHeight, clientHeight } = scrollEl;
            if (scrollHeight - scrollTop - clientHeight < 100) {
              onLoadMore();
            }
          }}
        >
          <div className="space-y-0.5 pb-2">
            {!collapsed && taskHistory.length === 0 && (
              <p className="px-3 py-3 text-xs text-muted-foreground">
                {searchQuery ? "No matching tasks." : "No tasks yet."}
              </p>
            )}
            {taskHistory.map((task) => {
              const isActive = task.id === activeTaskId;
              return collapsed ? (
                <Tooltip key={task.id}>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={() => onSelectTask?.(task.id)}
                      className={cn(
                        "flex w-full cursor-pointer items-center justify-center rounded-lg p-2 transition-all duration-150 hover:bg-card/80",
                        isActive && "bg-card/80 shadow-[var(--shadow-card)]",
                      )}
                    >
                      <div className={cn(
                        "h-1.5 w-1.5 shrink-0 rounded-full transition-colors",
                        isActive ? "bg-ai-glow" : "bg-muted-foreground/40",
                      )} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">{task.title}</TooltipContent>
                </Tooltip>
              ) : (
                <div
                  key={task.id}
                  role="button"
                  tabIndex={0}
                  aria-current={isActive ? "true" : undefined}
                  onClick={() => onSelectTask?.(task.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSelectTask?.(task.id);
                    }
                  }}
                  className={cn(
                    "group flex w-full cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2 text-left transition-colors duration-150",
                    "hover:bg-card/60 hover:backdrop-blur-sm",
                    isActive && "bg-card/80 shadow-card backdrop-blur-sm",
                  )}
                >
                  <div className={cn(
                    "h-1.5 w-1.5 shrink-0 rounded-full transition-colors",
                    isActive ? "bg-ai-glow" : "bg-muted-foreground/40",
                  )} />
                  <span className={cn(
                    "flex-1 truncate text-sm transition-colors",
                    isActive ? "text-foreground font-medium" : "text-muted-foreground",
                  )}>
                    {task.title}
                  </span>
                  {onDeleteTask && (
                    <button
                      type="button"
                      tabIndex={0}
                      aria-label={`Delete task: ${task.title}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setTaskToDelete(task);
                      }}
                      className="hidden shrink-0 rounded-md p-1 text-muted-foreground/50 hover:text-destructive hover:bg-destructive/10 group-hover:inline-flex focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 group-focus-within:inline-flex transition-all"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </div>

      {/* Footer: Integrations */}
      <div className={cn("relative border-t border-border/40", collapsed ? "px-2 py-2" : "px-3 py-2.5")}>
        {collapsed ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Link href="/integrations">
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="w-full text-muted-foreground hover:text-foreground hover:bg-card/80"
                  asChild
                >
                  <span>
                    <Blocks className="h-4 w-4" />
                  </span>
                </Button>
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right">Integrations</TooltipContent>
          </Tooltip>
        ) : (
          <Link
            href="/integrations"
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-all duration-150 hover:bg-card/60 hover:text-foreground"
          >
            <Blocks className="h-4 w-4" />
            Integrations
          </Link>
        )}
      </div>

      {/* Delete confirmation dialog */}
      <AlertDialog open={taskToDelete !== null} onOpenChange={(open) => { if (!open) setTaskToDelete(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete task</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &quot;{taskToDelete?.title}&quot;? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete} className="bg-destructive text-primary-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Drag handle for resizing */}
      {!collapsed && (
        <div
          onMouseDown={handleDragStart}
          className={cn(
            "absolute right-0 top-0 h-full w-1 cursor-col-resize hover:bg-primary/20 active:bg-primary/30",
            isDragging && "bg-primary/30",
          )}
        />
      )}
    </aside>
  );
}

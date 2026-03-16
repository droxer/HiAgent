"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import Image from "next/image";
import { Plus, PanelLeftClose, PanelLeftOpen, Search, X, Trash2 } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
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
  width = 280,
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
        "relative flex h-screen shrink-0 flex-col border-r border-border bg-card overflow-hidden",
        collapsed ? "w-12" : "",
        !collapsed && !isDragging && "transition-[width] duration-200 ease-in-out",
      )}
      style={collapsed ? undefined : { width }}
    >
      {/* Header: logo + collapse/expand toggle */}
      <div className={cn("flex items-center py-4", collapsed ? "flex-col gap-2 px-2" : "justify-between px-4")}>
        <div className="flex items-center gap-2.5">
          <Image
            src="/logo.png"
            alt="HiAgent logo"
            width={28}
            height={28}
            className="rounded-md shrink-0"
          />
          {!collapsed && (
            <span className="text-sm font-bold tracking-tight text-foreground whitespace-nowrap">
              HiAgent
            </span>
          )}
        </div>
        {onToggle && (
          collapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon-sm" onClick={onToggle} className="text-muted-foreground">
                  <PanelLeftOpen className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right">Expand sidebar</TooltipContent>
            </Tooltip>
          ) : (
            <Button variant="ghost" size="icon-sm" onClick={onToggle} className="text-muted-foreground">
              <PanelLeftClose className="h-4 w-4" />
            </Button>
          )
        )}
      </div>

      {/* New task button */}
      <div className={cn(collapsed ? "px-2 pb-2" : "px-3 pb-3")}>
        {collapsed ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                onClick={onNewTask}
                variant="ghost"
                className="w-full border border-transparent hover:border-border"
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
            variant="ghost"
            className="w-full justify-start gap-2 border border-transparent hover:border-border"
          >
            <Plus className="h-4 w-4" />
            New task
          </Button>
        )}
      </div>

      {/* Search input (expanded mode only) */}
      {!collapsed && onSearchChange && (
        <div className="px-3 pb-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="h-8 pl-8 pr-8 text-sm"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => onSearchChange("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Task list */}
      <div className={cn("min-h-0 flex-1", collapsed ? "px-2" : "px-3")}>
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
              <p className="px-2 py-3 text-xs text-muted-foreground">
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
                        "flex w-full cursor-pointer items-center justify-center p-2 transition-colors duration-150 hover:bg-muted",
                        isActive && "bg-muted",
                      )}
                    >
                      <div className="h-1 w-1 shrink-0 rounded-full bg-muted-foreground/50" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">{task.title}</TooltipContent>
                </Tooltip>
              ) : (
                <button
                  key={task.id}
                  type="button"
                  onClick={() => onSelectTask?.(task.id)}
                  className={cn(
                    "group flex w-full cursor-pointer items-center gap-2.5 rounded-md px-2 py-2 text-left transition-colors duration-150 hover:bg-muted",
                    isActive && "bg-muted",
                  )}
                >
                  <div className="h-1 w-1 shrink-0 rounded-full bg-muted-foreground/50" />
                  <span className="flex-1 truncate text-sm text-foreground">
                    {task.title}
                  </span>
                  {onDeleteTask && (
                    <span
                      role="button"
                      tabIndex={0}
                      onClick={(e) => {
                        e.stopPropagation();
                        setTaskToDelete(task);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.stopPropagation();
                          setTaskToDelete(task);
                        }
                      }}
                      className="hidden shrink-0 rounded p-0.5 text-muted-foreground hover:text-destructive group-hover:inline-flex"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </ScrollArea>
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
            <AlertDialogAction onClick={handleConfirmDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
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

"use client";

import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import { Plus, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { ScrollArea } from "@/shared/components/ui/scroll-area";
import { Separator } from "@/shared/components/ui/separator";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/shared/components/ui/tooltip";
import { cn } from "@/shared/lib/utils";
import type { ConversationHistoryItem } from "@/features/conversation/stores/conversation-store";

interface SidebarProps {
  taskHistory: readonly ConversationHistoryItem[];
  onNewTask: () => void;
  collapsed?: boolean;
  onToggle?: () => void;
}

const STATUS_DOT_COLORS: Record<ConversationHistoryItem["status"], string> = {
  running: "bg-amber-400",
  complete: "bg-emerald-500",
  error: "bg-rose-500",
};

const historyContainer = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.04,
    },
  },
};

const historyItem = {
  hidden: { opacity: 0, x: -8 },
  show: { opacity: 1, x: 0, transition: { duration: 0.15 } },
};

export function Sidebar({ taskHistory, onNewTask, collapsed = false, onToggle }: SidebarProps) {
  return (
    <aside
      className={cn(
        "flex h-screen shrink-0 flex-col border-r border-border bg-white transition-[width] duration-200 ease-in-out overflow-hidden",
        collapsed ? "w-[60px]" : "w-[260px]",
      )}
    >
      {/* Logo + collapse toggle */}
      <div className={cn("flex items-center py-5", collapsed ? "justify-center px-2" : "justify-between px-5")}>
        <div className="flex items-center gap-2.5">
          <Image
            src="/logo.png"
            alt="HiAgent"
            width={32}
            height={32}
            className="rounded-sm shrink-0"
          />
          {!collapsed && (
            <span className="text-base font-bold tracking-tight text-foreground whitespace-nowrap">
              HiAgent
            </span>
          )}
        </div>
        {!collapsed && onToggle && (
          <button
            type="button"
            onClick={onToggle}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted transition-colors"
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* New task button */}
      <div className={cn(collapsed ? "px-2 pb-2" : "px-3 pb-2")}>
        {collapsed ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                onClick={onNewTask}
                className="w-full"
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
            className="w-full justify-start gap-2"
            size="lg"
          >
            <Plus className="h-4 w-4" />
            New task
          </Button>
        )}
      </div>

      {/* All tasks section */}
      <div className={cn("mt-2 flex flex-1 flex-col overflow-hidden", collapsed ? "px-2" : "px-3")}>
        {!collapsed && (
          <div className="mb-2 flex items-center px-2">
            <span className="text-caption font-semibold uppercase tracking-wider text-muted-foreground whitespace-nowrap">
              All tasks
            </span>
          </div>
        )}

        {collapsed && <Separator className="mb-2" />}

        <ScrollArea className="flex-1">
          <motion.div
            className="space-y-0.5 pb-2"
            variants={historyContainer}
            initial="hidden"
            animate="show"
          >
            {!collapsed && taskHistory.length === 0 && (
              <p className="px-2 py-3 text-xs text-muted-foreground">
                No tasks yet. Start a new task above.
              </p>
            )}
            {taskHistory.map((task) =>
              collapsed ? (
                <Tooltip key={task.id}>
                  <TooltipTrigger asChild>
                    <motion.button
                      type="button"
                      className="flex w-full cursor-pointer items-center justify-center rounded-sm p-2 transition-colors hover:bg-muted"
                      variants={historyItem}
                    >
                      <div
                        className={cn(
                          "h-2.5 w-2.5 shrink-0 rounded-full",
                          STATUS_DOT_COLORS[task.status],
                        )}
                      />
                    </motion.button>
                  </TooltipTrigger>
                  <TooltipContent side="right">{task.title}</TooltipContent>
                </Tooltip>
              ) : (
                <motion.button
                  key={task.id}
                  type="button"
                  className="flex w-full cursor-pointer items-center gap-2.5 rounded-sm px-2 py-2 text-left transition-colors hover:bg-muted"
                  variants={historyItem}
                >
                  <div
                    className={cn(
                      "h-2 w-2 shrink-0 rounded-full",
                      STATUS_DOT_COLORS[task.status],
                    )}
                  />
                  <span className="flex-1 truncate text-sm text-foreground">
                    {task.title}
                  </span>
                </motion.button>
              ),
            )}
          </motion.div>
        </ScrollArea>
      </div>

      {/* Bottom: expand toggle (collapsed) or version (expanded) */}
      <Separator />
      {collapsed ? (
        <div className="flex justify-center py-3">
          {onToggle && (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={onToggle}
                  className="rounded-md p-1.5 text-muted-foreground hover:bg-muted transition-colors"
                >
                  <PanelLeftOpen className="h-4 w-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="right">Expand sidebar</TooltipContent>
            </Tooltip>
          )}
        </div>
      ) : (
        <div className="px-5 py-3">
          <span className="text-caption text-muted-foreground">v0.1.0</span>
        </div>
      )}
    </aside>
  );
}

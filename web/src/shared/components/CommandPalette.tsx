"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Command } from "cmdk";
import { AnimatePresence, motion } from "framer-motion";
import {
  Search,
  Plus,
  Sparkles,
  Globe,
  Presentation,
  AppWindow,
  Palette,
  Settings,
} from "lucide-react";

interface CommandPaletteProps {
  readonly onNewTask: (prompt: string) => void;
  readonly onNavigateHome?: () => void;
}

const QUICK_ACTIONS = [
  { icon: Sparkles, label: "Summarize Page", prompt: "Summarize this page" },
  { icon: Presentation, label: "Create Slides", prompt: "Create a presentation about " },
  { icon: Globe, label: "Build Website", prompt: "Build a website that " },
  { icon: AppWindow, label: "Develop App", prompt: "Develop an app that " },
  { icon: Palette, label: "Design UI", prompt: "Design a " },
] as const;

export function CommandPalette({ onNewTask, onNavigateHome }: CommandPaletteProps) {
  const [open, setOpen] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      setOpen((prev) => !prev);
    }
    if (e.key === "Escape") {
      setOpen(false);
    }
  }, []);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Focus trap: keep Tab cycling within the dialog when open
  useEffect(() => {
    if (!open) return;

    const handleTrap = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;
      const container = dialogRef.current;
      if (!container) return;

      const focusable = container.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleTrap);
    return () => document.removeEventListener("keydown", handleTrap);
  }, [open]);

  const handleSelect = (prompt: string) => {
    setOpen(false);
    onNewTask(prompt);
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop — stronger blur */}
          <motion.div
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-md"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={() => setOpen(false)}
          />

          {/* Command dialog — blur-to-sharp entry */}
          <motion.div
            ref={dialogRef}
            className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]"
            initial={{ opacity: 0, scale: 0.96, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -10 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
          >
            <Command
              className="w-full max-w-[560px] overflow-hidden rounded-xl border border-border bg-card/90 shadow-elevated backdrop-blur-xl"
              loop
            >
              {/* Search input */}
              <div className="flex items-center gap-2 border-b border-border px-4">
                <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
                <Command.Input
                  placeholder="Type a command or search..."
                  className="h-12 w-full bg-transparent text-sm text-foreground placeholder:text-placeholder outline-none"
                  autoFocus
                />
                <kbd className="shrink-0 rounded border border-border bg-secondary px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                  ESC
                </kbd>
              </div>

              <Command.List className="max-h-[320px] overflow-y-auto p-2">
                <Command.Empty className="px-4 py-8 text-center text-sm text-muted-foreground">
                  No results found.
                </Command.Empty>

                {/* Quick Actions */}
                <Command.Group heading="Quick Actions" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground">
                  {QUICK_ACTIONS.map((action) => (
                    <Command.Item
                      key={action.label}
                      value={action.label}
                      onSelect={() => handleSelect(action.prompt)}
                      className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-foreground/90 transition-colors data-[selected=true]:bg-secondary data-[selected=true]:text-foreground data-[selected=true]:border-l-2 data-[selected=true]:border-ai-glow"
                    >
                      <action.icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                      {action.label}
                    </Command.Item>
                  ))}
                </Command.Group>

                {/* Navigation */}
                <Command.Group heading="Navigation" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground">
                  <Command.Item
                    value="New Task"
                    onSelect={() => {
                      setOpen(false);
                      onNavigateHome?.();
                    }}
                    className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-foreground/90 transition-colors data-[selected=true]:bg-secondary data-[selected=true]:text-foreground data-[selected=true]:border-l-2 data-[selected=true]:border-ai-glow"
                  >
                    <Plus className="h-4 w-4 shrink-0 text-muted-foreground" />
                    New Task
                  </Command.Item>
                  <Command.Item
                    value="Settings"
                    onSelect={() => setOpen(false)}
                    className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-foreground/90 transition-colors data-[selected=true]:bg-secondary data-[selected=true]:text-foreground data-[selected=true]:border-l-2 data-[selected=true]:border-ai-glow"
                  >
                    <Settings className="h-4 w-4 shrink-0 text-muted-foreground" />
                    Settings
                  </Command.Item>
                </Command.Group>
              </Command.List>

              {/* Footer hint */}
              <div className="flex items-center justify-between border-t border-border px-4 py-2">
                <span className="text-xs text-muted-foreground">
                  Navigate with <kbd className="font-mono">↑↓</kbd> · Select with <kbd className="font-mono">↵</kbd>
                </span>
              </div>
            </Command>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

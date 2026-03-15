"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ArrowUp, Plus, Code2, Share2, Mic } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface ChatInputProps {
  readonly onSendMessage: (message: string) => void;
}

export function ChatInput({ onSendMessage }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resetHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, []);

  useEffect(() => {
    resetHeight();
  }, [input, resetHeight]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;
    onSendMessage(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const hasContent = input.trim().length > 0;

  return (
    <div className="shrink-0 border-t border-border p-4">
      <form onSubmit={handleSubmit}>
        <div className="rounded-2xl border border-border bg-card transition-all focus-within:border-border-active focus-within:shadow-sm">
          {/* Textarea */}
          <div className="px-4 pt-3 pb-1">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Send a message..."
              rows={1}
              className="w-full resize-none bg-transparent text-sm leading-relaxed text-foreground placeholder:text-text-muted outline-none"
            />
          </div>

          {/* Toolbar */}
          <div className="flex items-center justify-between px-2.5 pb-2.5">
            <div className="flex items-center gap-0.5">
              <ToolbarButton icon={Plus} label="Attach" />
              <ToolbarButton icon={Code2} label="Code" />
              <ToolbarButton icon={Share2} label="Share" />
              <ToolbarButton icon={Mic} label="Voice" />
            </div>

            <button
              type="submit"
              disabled={!hasContent}
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-full transition-all",
                hasContent
                  ? "bg-accent-emerald text-white hover:bg-accent-emerald/90 active:scale-95"
                  : "bg-muted text-text-muted cursor-not-allowed"
              )}
            >
              <ArrowUp className="h-4 w-4" strokeWidth={2.5} />
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

/* ─── Internal toolbar icon button ─── */

function ToolbarButton({
  icon: Icon,
  label,
  onClick,
}: {
  readonly icon: React.ComponentType<{ className?: string }>;
  readonly label: string;
  readonly onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      className="flex h-8 w-8 items-center justify-center rounded-lg text-text-secondary transition-colors hover:bg-muted hover:text-foreground"
    >
      <Icon className="h-[18px] w-[18px]" />
    </button>
  );
}

"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Square } from "lucide-react";
import { SendButton } from "@/shared/components/SendButton";
import { cn } from "@/shared/lib/utils";

interface ChatInputProps {
  readonly onSendMessage: (message: string) => void;
  readonly disabled?: boolean;
  readonly onCancel?: () => void;
  readonly isAgentRunning?: boolean;
}

export function ChatInput({ onSendMessage, disabled = false, onCancel, isAgentRunning = false }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
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
    if (disabled) return;
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
    <div className="shrink-0 px-4 pb-4 pt-2">
      <form onSubmit={handleSubmit}>
        <div
          className={cn(
            "relative rounded-xl backdrop-blur-sm bg-card/80 transition-all duration-200",
            isFocused
              ? "shadow-[0_0_0_1px_var(--color-border-active),0_4px_12px_rgba(0,0,0,0.3),0_0_20px_var(--color-input-glow)]"
              : "shadow-[0_0_0_1px_var(--color-border),0_1px_3px_rgba(0,0,0,0.2)]",
          )}
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={disabled ? "Agent is working..." : "Send a message..."}
            disabled={disabled}
            rows={1}
            className={cn(
              "w-full resize-none bg-transparent px-4 pt-3.5 pb-10 text-sm leading-relaxed text-foreground placeholder:text-placeholder outline-none",
              disabled && "opacity-50 cursor-not-allowed",
            )}
          />

          {/* Bottom bar: hint + action button */}
          <div className="absolute right-3 bottom-2.5 left-3 flex items-center justify-between">
            <span
              className={cn(
                "text-xs text-placeholder select-none transition-opacity duration-150",
                hasContent && !isAgentRunning ? "opacity-100" : "opacity-0",
              )}
            >
              <kbd className="font-mono text-[10px]">Enter</kbd> to send
              <span className="mx-1 text-border-strong">&middot;</span>
              <kbd className="font-mono text-[10px]">Shift + Enter</kbd> for new line
            </span>

            <div className="relative flex h-8 w-8 items-center justify-center">
              <AnimatePresence mode="wait">
                {isAgentRunning ? (
                  <motion.button
                    key="cancel"
                    type="button"
                    onClick={onCancel}
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.8, opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className={cn(
                      "group relative flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px]",
                      "bg-foreground/[0.06] text-muted-foreground",
                      "transition-all duration-200 ease-out",
                      "hover:bg-destructive/10 hover:text-destructive",
                      "active:scale-90 active:bg-destructive/15",
                      "focus-visible:ring-[3px] focus-visible:ring-ring/50 outline-none",
                    )}
                  >
                    {/* Conic-gradient spinning border */}
                    <span
                      className="absolute inset-0 rounded-[10px] opacity-60"
                      style={{
                        background: "conic-gradient(from 0deg, var(--color-ai-glow), transparent 60%, var(--color-ai-glow))",
                        mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
                        maskComposite: "exclude",
                        WebkitMaskComposite: "xor",
                        padding: "1px",
                        animation: "conicSpin 3s linear infinite",
                      }}
                    />
                    <Square
                      className="relative h-3.5 w-3.5 transition-transform duration-200 group-hover:scale-110"
                      fill="currentColor"
                      strokeWidth={0}
                    />
                  </motion.button>
                ) : (
                  <SendButton
                    key="send"
                    disabled={disabled}
                    hasContent={hasContent}
                  />
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}

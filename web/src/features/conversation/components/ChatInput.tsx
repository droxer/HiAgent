"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Square, Paperclip, ArrowUp } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { FileAttachmentChip } from "@/shared/components/FileAttachmentChip";
import { SkillSelector } from "@/features/skills";
import { cn } from "@/shared/lib/utils";
import { useTranslation } from "@/i18n";
import type { AttachedFile } from "@/shared/types";

interface ChatInputProps {
  readonly onSendMessage: (message: string, files?: File[], skills?: string[]) => void;
  readonly disabled?: boolean;
  readonly onCancel?: () => void;
  readonly isAgentRunning?: boolean;
  readonly variant?: "default" | "welcome";
  readonly autoFocus?: boolean;
}

export function ChatInput({ onSendMessage, disabled = false, onCancel, isAgentRunning = false, variant = "default", autoFocus = false }: ChatInputProps) {
  const { t } = useTranslation();
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const resetHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, []);

  useEffect(() => {
    resetHeight();
  }, [input, resetHeight]);

  const addFiles = useCallback((fileList: FileList | File[]) => {
    const newFiles: AttachedFile[] = Array.from(fileList).map((file) => ({
      file,
      id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
      previewUrl: file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined,
    }));
    setAttachedFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const removeFile = useCallback((id: string) => {
    setAttachedFiles((prev) => {
      const file = prev.find((f) => f.id === id);
      if (file?.previewUrl) URL.revokeObjectURL(file.previewUrl);
      return prev.filter((f) => f.id !== id);
    });
  }, []);

  // Cleanup URLs on unmount
  useEffect(() => {
    return () => {
      attachedFiles.forEach((f) => {
        if (f.previewUrl) URL.revokeObjectURL(f.previewUrl);
      });
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (disabled) return;
    const trimmed = input.trim();
    if (!trimmed && attachedFiles.length === 0) return;
    const files = attachedFiles.length > 0 ? attachedFiles.map((f) => f.file) : undefined;
    const skills = selectedSkill ? [selectedSkill] : undefined;
    onSendMessage(trimmed || t("chat.defaultFileMessage"), files, skills);
    setInput("");
    setAttachedFiles([]);
    setSelectedSkill(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  }, [addFiles]);

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const items = e.clipboardData.items;
    const imageFiles: File[] = [];
    for (const item of items) {
      if (item.type.startsWith("image/")) {
        const file = item.getAsFile();
        if (file) imageFiles.push(file);
      }
    }
    if (imageFiles.length > 0) {
      addFiles(imageFiles);
    }
  }, [addFiles]);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
    }
    // Reset so the same file can be selected again
    e.target.value = "";
  }, [addFiles]);

  const hasContent = input.trim().length > 0 || attachedFiles.length > 0;
  const hasAttachments = selectedSkill || attachedFiles.length > 0;
  const isWelcome = variant === "welcome";

  return (
    <div className={cn(!isWelcome && "shrink-0 px-4 pb-4 pt-2")}>
      <form
        onSubmit={handleSubmit}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileInputChange}
        />

        <div
          className={cn(
            "relative rounded-lg bg-card border transition-all duration-200",
            isFocused
              ? "border-border-active shadow-md"
              : "border-border shadow-sm",
            isDragOver && "border-dashed border-border-active bg-secondary/30",
          )}
        >
          {/* File & skill attachment shelf */}
          <AnimatePresence>
            {hasAttachments && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="overflow-hidden"
              >
                <div className="flex flex-wrap items-center gap-1.5 px-4 pt-3 pb-1">
                  <SkillSelector
                    selectedSkill={selectedSkill}
                    onSelect={setSelectedSkill}
                    buttonSize="icon-xs"
                  />
                  <AnimatePresence>
                    {attachedFiles.map((af) => (
                      <motion.div
                        key={af.id}
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -4 }}
                        transition={{ duration: 0.15 }}
                      >
                        <FileAttachmentChip
                          name={af.file.name}
                          size={af.file.size}
                          previewUrl={af.previewUrl}
                          onRemove={() => removeFile(af.id)}
                        />
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onPaste={handlePaste}
            placeholder={disabled ? t("chat.placeholderWorking") : t("chat.placeholder")}
            disabled={disabled}
            rows={isWelcome ? 3 : 1}
            autoFocus={autoFocus || isWelcome}
            className={cn(
              "w-full resize-none bg-transparent px-4 pt-3 pb-3 text-sm leading-relaxed text-foreground placeholder:text-placeholder outline-none",
              disabled && "opacity-50 cursor-not-allowed",
            )}
          />

          {/* Toolbar divider + action bar */}
          <div className="border-t border-border/40 px-3 py-2 flex items-center justify-between gap-2">
            {/* Left: tools + hints */}
            <div className="flex items-center gap-0.5">
              <Button
                type="button"
                variant="ghost"
                size="icon-xs"
                aria-label={t("chat.attachFile")}
                onClick={() => fileInputRef.current?.click()}
                className="text-muted-foreground-dim hover:bg-secondary hover:text-muted-foreground"
              >
                <Paperclip className="h-3.5 w-3.5" />
              </Button>

              {!selectedSkill && (
                <SkillSelector
                  selectedSkill={selectedSkill}
                  onSelect={setSelectedSkill}
                  buttonSize="icon-xs"
                />
              )}

              {!isWelcome && (
                <span
                  className={cn(
                    "ml-1 text-xs text-muted-foreground-dim select-none transition-opacity duration-150",
                    hasContent && !isAgentRunning ? "opacity-100" : "opacity-0",
                  )}
                >
                  <kbd className="rounded border border-border bg-secondary/60 px-1 py-0.5 font-mono text-[0.625rem] text-muted-foreground">Enter</kbd>
                  <span className="mx-1 text-muted-foreground-dim">{t("chat.enterToSend")}</span>
                  <kbd className="rounded border border-border bg-secondary/60 px-1 py-0.5 font-mono text-[0.625rem] text-muted-foreground">Shift+Enter</kbd>
                  <span className="ml-1 text-muted-foreground-dim">{t("chat.shiftEnterNewLine")}</span>
                </span>
              )}
            </div>

            {/* Right: send / cancel */}
            <AnimatePresence mode="wait">
              {isAgentRunning ? (
                <motion.button
                  key="cancel"
                  type="button"
                  onClick={onCancel}
                  aria-label={t("chat.cancelExecution")}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className={cn(
                    "group flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                    "bg-muted text-muted-foreground",
                    "transition-colors duration-200 ease-out",
                    "hover:bg-destructive/10 hover:text-destructive",
                    "active:bg-destructive/15",
                    "focus-visible:ring-[3px] focus-visible:ring-ring/50 outline-none",
                  )}
                >
                  <Square
                    className="h-3 w-3 transition-transform duration-200 group-hover:scale-110"
                    fill="currentColor"
                    strokeWidth={0}
                  />
                </motion.button>
              ) : (
                <motion.button
                  key="send"
                  type="submit"
                  disabled={disabled || !hasContent}
                  aria-label={hasContent ? t("chat.sendMessage") : t("chat.typeToSend")}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: hasContent ? 1 : 0.4 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className={cn(
                    "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                    "transition-colors duration-200 ease-out",
                    "focus-visible:ring-[3px] focus-visible:ring-ring/50 outline-none",
                    hasContent
                      ? "bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/80"
                      : "bg-muted text-placeholder cursor-default",
                  )}
                >
                  <ArrowUp className="h-3.5 w-3.5" strokeWidth={2.5} />
                </motion.button>
              )}
            </AnimatePresence>
          </div>
        </div>
      </form>
    </div>
  );
}

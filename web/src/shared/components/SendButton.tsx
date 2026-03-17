"use client";

import { motion } from "framer-motion";
import { ArrowUp } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface SendButtonProps {
  readonly disabled?: boolean;
  readonly hasContent?: boolean;
}

export function SendButton({ disabled = false, hasContent = false }: SendButtonProps) {
  return (
    <motion.button
      type="submit"
      disabled={disabled || !hasContent}
      initial={{ scale: 0.85, opacity: 0 }}
      animate={{
        scale: hasContent ? 1 : 0.85,
        opacity: hasContent ? 1 : 0.5,
      }}
      exit={{ scale: 0.85, opacity: 0 }}
      transition={{ type: "spring", stiffness: 400, damping: 20 }}
      className={cn(
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
        "transition-colors transition-shadow transition-transform duration-200 ease-out",
        "focus-visible:ring-[3px] focus-visible:ring-ring/50 outline-none",
        hasContent
          ? [
              "bg-primary text-primary-foreground",
              "shadow-card",
              "hover:shadow-card-hover hover:translate-y-[-1px]",
              "active:translate-y-[1px] active:shadow-none",
            ]
          : "bg-transparent text-placeholder/40 cursor-default",
      )}
    >
      <ArrowUp
        className="h-3.5 w-3.5 transition-transform duration-200"
        strokeWidth={2.5}
      />
    </motion.button>
  );
}

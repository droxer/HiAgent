"use client";

import { motion } from "framer-motion";
import { cn } from "@/shared/lib/utils";

interface PulsingDotProps {
  readonly size?: "sm" | "md";
  readonly className?: string;
}

export function PulsingDot({ size = "sm", className }: PulsingDotProps) {
  const sizeClass = size === "md" ? "h-2 w-2" : "h-1.5 w-1.5";

  return (
    <span className={cn("relative shrink-0", sizeClass, className)}>
      <motion.span
        className={cn("absolute inset-0 rounded-full bg-ai-glow")}
        animate={{ opacity: [1, 0.4, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      />
      <span
        className="absolute inset-0 rounded-full bg-ai-glow"
        style={{ animation: "orbitalPulse 2s ease-out infinite" }}
      />
    </span>
  );
}

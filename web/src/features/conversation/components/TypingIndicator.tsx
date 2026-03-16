"use client";

import { motion } from "framer-motion";

const DOT_INDICES = [0, 1, 2] as const;

export function TypingIndicator() {
  return (
    <motion.div
      className="flex justify-start"
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
    >
      <div
        className="inline-flex items-center gap-1 rounded-full border border-border bg-card px-3.5 py-2"
        style={{ boxShadow: "var(--shadow-card)" }}
      >
        {DOT_INDICES.map((i) => (
          <motion.span
            key={i}
            className="h-1.5 w-1.5 rounded-full bg-accent-emerald"
            animate={{
              scale: [1, 1.4, 1],
              opacity: [0.4, 1, 0.4],
            }}
            transition={{
              duration: 1.4,
              repeat: Infinity,
              delay: i * 0.2,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
    </motion.div>
  );
}

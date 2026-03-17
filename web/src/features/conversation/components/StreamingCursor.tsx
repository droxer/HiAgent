"use client";

import { motion } from "framer-motion";

export function StreamingCursor() {
  return (
    <motion.span
      className="ml-1 inline-block h-4 w-[3px] rounded-full bg-ai-glow align-middle"
      initial={{ opacity: 1 }}
      animate={{ opacity: [1, 0.4, 1] }}
      exit={{ opacity: 0, transition: { duration: 0.15 } }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: "easeInOut",
      }}
      aria-hidden="true"
    />
  );
}

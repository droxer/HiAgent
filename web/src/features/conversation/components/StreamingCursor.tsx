"use client";

import { motion } from "framer-motion";

export function StreamingCursor() {
  return (
    <motion.span
      className="ml-0.5 inline-block h-4 w-0.5 rounded-full bg-foreground/60 align-middle"
      initial={{ opacity: 1 }}
      animate={{ opacity: [1, 0.3, 1] }}
      exit={{ opacity: 0, transition: { duration: 0.2 } }}
      transition={{
        opacity: {
          duration: 0.9,
          repeat: Infinity,
          ease: "easeInOut",
        },
      }}
      aria-hidden="true"
    />
  );
}

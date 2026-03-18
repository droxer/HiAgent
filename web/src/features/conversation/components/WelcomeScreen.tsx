"use client";

import { motion } from "framer-motion";
import { ChatInput } from "./ChatInput";
import { useTranslation } from "@/i18n";

interface WelcomeScreenProps {
  onSubmitTask: (task: string, files?: File[], skills?: string[]) => void;
}

export function WelcomeScreen({ onSubmitTask }: WelcomeScreenProps) {
  const { tArray } = useTranslation();
  const headingWords = tArray("welcome.headingWords");
  return (
    <div className="relative flex h-full w-full flex-col items-center justify-center overflow-hidden px-4 sm:px-6">
      {/* Subtle warm radial background */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background: "radial-gradient(ellipse 70% 50% at 50% 45%, var(--color-ai-surface) 0%, transparent 70%)",
        }}
      />

      <motion.div
        className="relative z-10 flex w-full max-w-3xl flex-col items-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        {/* Staggered word reveal heading */}
        <h1 className="mb-10 text-center font-serif text-[2rem] font-semibold leading-[1.15] tracking-tight text-foreground sm:text-[2.75rem] md:text-[3.25rem]">
          {headingWords.map((word, i) => (
            <motion.span
              key={i}
              className="inline-block mr-[0.3em]"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                duration: 0.35,
                delay: i * 0.08,
                ease: "easeOut",
              }}
            >
              {word}
            </motion.span>
          ))}
        </h1>

        {/* Input card — delegates to ChatInput with welcome variant */}
        <div className="mb-6 w-full">
          <ChatInput
            onSendMessage={onSubmitTask}
            variant="welcome"
          />
        </div>
      </motion.div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowUp,
  Presentation,
  Globe,
  AppWindow,
  Palette,
  MoreHorizontal,
} from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { IconButton } from "@/shared/components/IconButton";
import { Textarea } from "@/shared/components/ui/textarea";

interface WelcomeScreenProps {
  onSubmitTask: (task: string) => void;
}

const QUICK_ACTIONS = [
  { icon: Presentation, label: "Create slides", prompt: "Create a presentation about " },
  { icon: Globe, label: "Build website", prompt: "Build a website that " },
  { icon: AppWindow, label: "Develop apps", prompt: "Develop an app that " },
  { icon: Palette, label: "Design", prompt: "Design a " },
  { icon: MoreHorizontal, label: "More", prompt: "" },
] as const;

const pillContainer = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.1,
    },
  },
};

const pillItem = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: 0.15 } },
};

export function WelcomeScreen({ onSubmitTask }: WelcomeScreenProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;
    onSubmitTask(trimmed);
    setInput("");
  };

  const handleQuickAction = (prompt: string) => {
    if (prompt) {
      setInput(prompt);
    }
  };

  return (
    <div className="relative flex h-full w-full flex-col items-center justify-center overflow-hidden px-6">
      <motion.div
        className="relative z-10 flex w-full max-w-2xl flex-col items-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
        {/* Main heading */}
        <h1 className="mb-10 text-center text-hero font-bold tracking-tight text-foreground font-sans">
          What can I do for you?
        </h1>

        {/* Input area */}
        <form onSubmit={handleSubmit} className="mb-6 w-full">
          <div className="rounded-lg border border-border bg-card shadow-sm transition-shadow duration-200 focus-within:shadow-md focus-within:border-border-default">
            {/* Textarea */}
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Assign a task or ask anything"
              rows={3}
              className="resize-none rounded-b-none border-0 bg-transparent px-5 pt-4 pb-2 text-sm text-foreground placeholder:text-muted-foreground shadow-none focus-visible:ring-0"
              autoFocus
            />

            {/* Bottom action bar */}
            <div className="flex items-center justify-end px-3 pb-3">
              <IconButton
                icon={ArrowUp}
                label="Send"
                type="submit"
                variant="default"
                disabled={!input.trim()}
                className=""
              />
            </div>
          </div>
        </form>

        {/* Quick action pills */}
        <motion.div
          className="flex flex-wrap justify-center gap-2"
          variants={pillContainer}
          initial="hidden"
          animate="show"
        >
          {QUICK_ACTIONS.map((action) => (
            <motion.div
              key={action.label}
              variants={pillItem}
            >
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleQuickAction(action.prompt)}
                className="gap-1.5 rounded-sm"
              >
                <action.icon className="h-3.5 w-3.5" />
                {action.label}
              </Button>
            </motion.div>
          ))}
        </motion.div>
      </motion.div>
    </div>
  );
}

"use client";

interface SuggestedCardProps {
  readonly text: string;
}

export function SuggestedCard({ text }: SuggestedCardProps) {
  return (
    <button
      type="button"
      className="cursor-pointer rounded-sm border border-border bg-card p-3 text-left text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
    >
      {text}
    </button>
  );
}

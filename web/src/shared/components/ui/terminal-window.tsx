import { cn } from "@/shared/lib/utils";

/**
 * Strip ANSI escape sequences from terminal output.
 * Handles SGR (colors/styles), cursor movement, erase, OSC, and other CSI codes.
 */
// eslint-disable-next-line no-control-regex
const ANSI_RE = /[\u001b\u009b][\[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><~]/g;

export function stripAnsi(text: string): string {
  return text.replace(ANSI_RE, "");
}

interface TerminalWindowProps {
  readonly title: string;
  readonly children: React.ReactNode;
  readonly className?: string;
}

export function TerminalWindow({ title, children, className }: TerminalWindowProps) {
  return (
    <div className={cn("overflow-hidden rounded-lg border border-[var(--color-terminal-border)]", className)}>
      {/* Title bar with traffic-light dots */}
      <div className="flex items-center gap-2 bg-[var(--color-terminal-surface)] px-3 py-2">
        <div className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-full bg-[#ff5f57]" />
          <span className="inline-block h-3 w-3 rounded-full bg-[#febc2e]" />
          <span className="inline-block h-3 w-3 rounded-full bg-[#28c840]" />
        </div>
        <span className="flex-1 text-center font-mono text-xs text-[var(--color-terminal-dim)]">
          {title}
        </span>
        {/* Spacer to balance traffic lights */}
        <div className="w-[54px]" />
      </div>

      {/* Terminal body */}
      <div className="bg-[var(--color-terminal-bg)] px-4 py-3 font-mono text-xs leading-relaxed">
        {children}
      </div>
    </div>
  );
}

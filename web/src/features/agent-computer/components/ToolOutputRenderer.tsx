"use client";

import { useState, useCallback } from "react";
import { ChevronDown, ChevronUp, Copy, Check, Image as ImageIcon, FileText } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { CODE_TOOLS } from "../lib/tool-constants";

/** Max chars to show before collapsing */
const COLLAPSE_THRESHOLD = 500;

interface ToolOutputRendererProps {
  readonly output: string;
  readonly toolName: string;
  readonly contentType?: string;
  readonly conversationId?: string | null;
  readonly artifactIds?: string[];
}

export function ToolOutputRenderer({ output, toolName, contentType, conversationId, artifactIds }: ToolOutputRendererProps) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const isLong = output.length > COLLAPSE_THRESHOLD;
  const isCode = CODE_TOOLS.has(toolName) || contentType?.startsWith("text/x-") || contentType?.startsWith("text/javascript");
  const isImage = contentType?.startsWith("image/");
  const isHtml = contentType === "text/html";

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(output);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access denied — silently degrade
    }
  }, [output]);

  const handleToggle = useCallback(() => setExpanded((p) => !p), []);

  const displayText = isLong && !expanded ? output.slice(0, COLLAPSE_THRESHOLD) : output;

  // Image artifact rendering — render from artifact endpoint, data URI, or HTTP URL
  if (isImage) {
    const hasArtifacts = artifactIds && artifactIds.length > 0 && conversationId;
    const looksLikeUri = output.startsWith("data:") || output.startsWith("http");
    return (
      <div className="mt-2.5 rounded-md bg-muted/60 p-3">
        <div className="mb-2 flex items-center gap-1.5 text-xs text-muted-foreground">
          <ImageIcon className="h-3 w-3" />
          <span>Image output</span>
        </div>
        <div className="flex flex-col items-center gap-3 rounded border border-border bg-background p-2">
          {hasArtifacts ? (
            artifactIds.map((aid) => (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img
                key={aid}
                src={`/api/conversations/${conversationId}/artifacts/${aid}`}
                alt="Generated image"
                className="max-h-80 rounded object-contain"
              />
            ))
          ) : looksLikeUri ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img src={output} alt="Agent output" className="max-h-80 rounded object-contain" />
          ) : (
            <p className="text-xs text-muted-foreground italic">
              Image artifact available (use artifact viewer to display)
            </p>
          )}
        </div>
        {!hasArtifacts && !looksLikeUri && (
          <pre className="mt-2 whitespace-pre-wrap font-mono text-xs leading-relaxed text-muted-foreground">
            {displayText}
          </pre>
        )}
      </div>
    );
  }

  // HTML content rendering
  if (isHtml) {
    return (
      <div className="mt-2.5 rounded-md bg-muted/60 p-3">
        <div className="mb-2 flex items-center gap-1.5 text-xs text-muted-foreground">
          <FileText className="h-3 w-3" />
          <span>HTML output</span>
        </div>
        <div className="rounded border border-border bg-background p-2">
          <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-muted-foreground">
            {displayText}
            {isLong && !expanded && "..."}
          </pre>
        </div>
        {isLong && <ExpandToggle expanded={expanded} onToggle={handleToggle} />}
      </div>
    );
  }

  return (
    <div className="mt-2.5 rounded-md bg-muted/60 px-3 py-2">
      {/* Copy button for code outputs */}
      {isCode && output.length > 50 && (
        <div className="mb-1.5 flex justify-end">
          <button
            type="button"
            onClick={handleCopy}
            aria-label={copied ? "Copied" : "Copy to clipboard"}
            className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                Copy
              </>
            )}
          </button>
        </div>
      )}

      <pre
        className={cn(
          "whitespace-pre-wrap font-mono text-xs leading-relaxed text-muted-foreground",
          isCode && "text-emerald-700 dark:text-emerald-400",
        )}
      >
        {displayText}
        {isLong && !expanded && (
          <span className="text-muted-foreground/50">{"\n..."}</span>
        )}
      </pre>

      {isLong && <ExpandToggle expanded={expanded} onToggle={handleToggle} />}
    </div>
  );
}

function ExpandToggle({
  expanded,
  onToggle,
}: {
  readonly expanded: boolean;
  readonly onToggle: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="mt-1.5 flex items-center gap-1 text-[11px] font-medium text-muted-foreground transition-colors hover:text-foreground"
    >
      {expanded ? (
        <>
          <ChevronUp className="h-3 w-3" />
          Show less
        </>
      ) : (
        <>
          <ChevronDown className="h-3 w-3" />
          Show more
        </>
      )}
    </button>
  );
}

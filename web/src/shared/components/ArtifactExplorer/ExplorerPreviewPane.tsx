"use client";

import React, { Component, useCallback } from "react";
import { Download, FileX } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { FilePreview } from "@/shared/components/FilePreview";
import { useTranslation } from "@/i18n";
import {
  fileIcon,
  fileCategoryColor,
  fileExtension,
  fileCategory,
  formatFileSize,
  isPreviewable,
} from "@/features/agent-computer/lib/artifact-helpers";
import type { ArtifactExplorerItem } from "./artifactExplorerUtils";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface ExplorerPreviewPaneProps {
  readonly item: ArtifactExplorerItem | null;
  readonly artifactUrl: string | null;
  readonly onDownload: (item: ArtifactExplorerItem) => void;
  readonly className?: string;
}

// ---------------------------------------------------------------------------
// Error boundary for FilePreview
// ---------------------------------------------------------------------------

interface PreviewErrorBoundaryState {
  readonly hasError: boolean;
}

interface PreviewErrorBoundaryProps {
  readonly children: React.ReactNode;
  readonly fallback: React.ReactNode;
}

class PreviewErrorBoundary extends Component<
  PreviewErrorBoundaryProps,
  PreviewErrorBoundaryState
> {
  constructor(props: PreviewErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): PreviewErrorBoundaryState {
    return { hasError: true };
  }

  override componentDidCatch(error: Error, info: React.ErrorInfo): void {
    console.error("[ExplorerPreviewPane] FilePreview error:", error, info.componentStack);
  }

  override render(): React.ReactNode {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// ---------------------------------------------------------------------------
// No-item placeholder
// ---------------------------------------------------------------------------

function SelectFilePlaceholder() {
  const { t } = useTranslation();

  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-muted-foreground">
      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-secondary">
        <FileX className="h-5 w-5 text-muted-foreground-dim" />
      </div>
      <p className="text-center text-sm">{t("explorer.selectFile")}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Preview unavailable fallback
// ---------------------------------------------------------------------------

interface PreviewUnavailableFallbackProps {
  readonly onDownload: () => void;
}

function PreviewUnavailableFallback({ onDownload }: PreviewUnavailableFallbackProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-3 p-6 text-muted-foreground">
      <p className="text-sm">{t("explorer.noPreview")}</p>
      <Button variant="outline" size="sm" onClick={onDownload}>
        <Download className="mr-1.5 h-3.5 w-3.5" />
        {t("explorer.downloadFile")}
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Public component
// ---------------------------------------------------------------------------

export function ExplorerPreviewPane({
  item,
  artifactUrl,
  onDownload,
  className,
}: ExplorerPreviewPaneProps) {
  const { t } = useTranslation();

  // Must be before any early return to comply with rules-of-hooks
  const handleDownload = useCallback(() => {
    if (item) onDownload(item);
  }, [onDownload, item]);

  if (item === null) {
    return (
      <div className={className}>
        <SelectFilePlaceholder />
      </div>
    );
  }

  const Icon = fileIcon(item.contentType);
  const colors = fileCategoryColor(item.contentType);
  const ext = fileExtension(item.name);
  const category = fileCategory(item.contentType, t);
  const canPreview = isPreviewable(item.contentType);

  const previewBody =
    artifactUrl && canPreview ? (
      <PreviewErrorBoundary fallback={<PreviewUnavailableFallback onDownload={handleDownload} />}>
        <div className="flex-1 overflow-auto">
          <FilePreview
            url={artifactUrl}
            contentType={item.contentType}
            fileName={item.name}
            onDownload={handleDownload}
          />
        </div>
      </PreviewErrorBoundary>
    ) : (
      <PreviewUnavailableFallback onDownload={handleDownload} />
    );

  return (
    <div className={`flex flex-col ${className ?? ""}`}>
      {/* Header */}
      <div className="flex items-start gap-3 border-b border-border p-4 shrink-0">
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${colors.bg}`}
        >
          <Icon className={`h-4 w-4 ${colors.icon}`} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <p
              className="truncate text-sm font-medium text-foreground"
              title={item.name}
            >
              {item.name}
            </p>
            {ext && (
              <span className="shrink-0 rounded bg-muted px-1 py-0.5 font-mono text-micro uppercase text-muted-foreground">
                {ext}
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            {category} &middot; {formatFileSize(item.size, t)}
          </p>
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {previewBody}
      </div>

      {/* Footer */}
      <div className="shrink-0 border-t border-border p-3">
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={handleDownload}
        >
          <Download className="mr-1.5 h-3.5 w-3.5" />
          {t("explorer.downloadFile")}
        </Button>
      </div>
    </div>
  );
}

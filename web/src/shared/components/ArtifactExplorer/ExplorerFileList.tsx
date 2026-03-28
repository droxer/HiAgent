"use client";

import { useRef, useCallback } from "react";
import { Download, Eye } from "lucide-react";
import { motion } from "framer-motion";
import { useTranslation } from "@/i18n";
import { IconButton } from "@/shared/components/IconButton";
import {
  fileIcon,
  fileCategory,
  fileExtension,
  fileCategoryColor,
  fileCategoryBorderColor,
  isPreviewable,
  formatFileSize,
} from "@/features/agent-computer/lib/artifact-helpers";
import { buildArtifactUrl } from "./artifactExplorerUtils";
import type { ArtifactExplorerItem } from "./artifactExplorerUtils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ExplorerFileListProps {
  items: readonly ArtifactExplorerItem[];
  selectedFileId: string | null;
  /** For panel mode — used to construct the artifact URL */
  conversationId?: string;
  onSelectFile: (id: string) => void;
  onPreview: (item: ArtifactExplorerItem) => void;
  onDownload: (item: ArtifactExplorerItem) => void;
  mode: "panel" | "page";
}

// ---------------------------------------------------------------------------
// Single file row
// ---------------------------------------------------------------------------

interface FileRowProps {
  item: ArtifactExplorerItem;
  index: number;
  isSelected: boolean;
  conversationId?: string;
  onSelectFile: (id: string) => void;
  onPreview: (item: ArtifactExplorerItem) => void;
  onDownload: (item: ArtifactExplorerItem) => void;
}

function FileRow({
  item,
  index,
  isSelected,
  conversationId,
  onSelectFile,
  onPreview,
  onDownload,
}: FileRowProps) {
  const { t } = useTranslation();

  const Icon = fileIcon(item.contentType);
  const category = fileCategory(item.contentType, t);
  const colors = fileCategoryColor(item.contentType);
  const ext = fileExtension(item.name);
  const canPreview = isPreviewable(item.contentType);
  const isImage = item.contentType.startsWith("image/");
  const artifactUrl = buildArtifactUrl(item, conversationId);

  const handleRowClick = useCallback(() => {
    onSelectFile(item.id);
  }, [item.id, onSelectFile]);

  const handlePreviewClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onPreview(item);
    },
    [item, onPreview],
  );

  // No-arg variants for IconButton (parent div already stops propagation)
  const handlePreviewButtonClick = useCallback(() => {
    onPreview(item);
  }, [item, onPreview]);

  const handleDownloadButtonClick = useCallback(() => {
    onDownload(item);
  }, [item, onDownload]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        if (canPreview) {
          onPreview(item);
        } else {
          onDownload(item);
        }
      } else if (e.key === " ") {
        e.preventDefault();
        onDownload(item);
      }
    },
    [item, canPreview, onPreview, onDownload],
  );

  return (
    <motion.div
      role="button"
      className={`group flex items-center gap-3 rounded-md border border-l-2 p-3 cursor-pointer transition-colors ${
        isSelected
          ? "border-border bg-secondary"
          : "border-border bg-card hover:bg-secondary/70"
      }`}
      style={{ borderLeftColor: fileCategoryBorderColor(item.contentType) }}
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15, delay: Math.min(index * 0.03, 0.3) }}
      onClick={handleRowClick}
      tabIndex={0}
      aria-selected={isSelected}
      onKeyDown={handleKeyDown}
    >
      {/* Icon box */}
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md ${colors.bg}`}
      >
        <Icon className={`h-4 w-4 ${colors.icon}`} />
      </div>

      {/* File info */}
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

      {/* Hover action buttons */}
      <div
        className="flex shrink-0 items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
        onClick={(e) => e.stopPropagation()}
      >
        {canPreview && (
          <IconButton
            icon={Eye}
            label={t("artifacts.preview")}
            size="icon-xs"
            onClick={handlePreviewButtonClick}
          />
        )}
        <IconButton
          icon={Download}
          label={t("artifacts.download")}
          size="icon-xs"
          onClick={handleDownloadButtonClick}
        />
      </div>

      {/* Image thumbnail */}
      {isImage && artifactUrl && (
        <div className="shrink-0" onClick={handlePreviewClick}>
          <img
            src={artifactUrl}
            alt={item.name}
            className="h-9 w-9 rounded-md border border-border object-cover"
          />
        </div>
      )}
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Public component
// ---------------------------------------------------------------------------

export function ExplorerFileList({
  items,
  selectedFileId,
  conversationId,
  onSelectFile,
  onPreview,
  onDownload,
  mode,
}: ExplorerFileListProps) {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);

  const handleContainerKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;

      const currentIndex = items.findIndex((item) => item.id === selectedFileId);
      let nextIndex: number;

      if (e.key === "ArrowDown") {
        nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
      } else {
        nextIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
      }

      const nextItem = items[nextIndex];
      if (nextItem) {
        e.preventDefault();
        onSelectFile(nextItem.id);

        // Focus the newly-selected row
        const rows = containerRef.current?.querySelectorAll<HTMLElement>(
          "[role='button']",
        );
        rows?.[nextIndex]?.focus();
      }
    },
    [items, selectedFileId, onSelectFile],
  );

  if (items.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 px-5">
        <p className="text-xs text-muted-foreground">{t("explorer.emptyFolder")}</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`h-full overflow-y-auto ${mode === "panel" ? "space-y-2 px-5 py-4" : "space-y-2 p-4"}`}
      onKeyDown={handleContainerKeyDown}
      aria-label={t("explorer.fileListLabel")}
    >
      {items.map((item, i) => (
        <FileRow
          key={item.id}
          item={item}
          index={i}
          isSelected={selectedFileId === item.id}
          conversationId={conversationId}
          onSelectFile={onSelectFile}
          onPreview={onPreview}
          onDownload={onDownload}
        />
      ))}
    </div>
  );
}

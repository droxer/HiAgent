"use client";

import { useCallback, useMemo } from "react";
import { FolderOpen } from "lucide-react";
import { useTranslation } from "@/i18n";
import { EmptyState } from "@/shared/components/EmptyState";
import { downloadFile } from "@/shared/lib/download";
import { ArtifactPreviewDialog } from "@/features/agent-computer/components/ArtifactPreviewDialog";
import { ExplorerSidebar } from "./ExplorerSidebar";
import { ExplorerFileList } from "./ExplorerFileList";
import { ExplorerPreviewPane } from "./ExplorerPreviewPane";
import {
  groupArtifactsByType,
  groupByConversation,
  classifyContentType,
  buildArtifactUrl,
} from "./artifactExplorerUtils";
import { useArtifactExplorer } from "./useArtifactExplorer";
import type { ArtifactExplorerItem, FolderNode, ConversationNode } from "./artifactExplorerUtils";
import type { LibraryGroup } from "@/features/library/types";
import type { ArtifactInfo } from "@/shared/types";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface ArtifactExplorerProps {
  /** Panel mode: pass raw artifact items from SSE events */
  readonly artifacts?: readonly ArtifactInfo[];
  readonly conversationId?: string | null;
  /** Page mode: pass library groups */
  readonly groups?: readonly LibraryGroup[];
  readonly mode: "panel" | "page";
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function filterItemsForFolder(
  allItems: readonly ArtifactExplorerItem[],
  selectedFolderId: string | null,
  mode: "panel" | "page",
): readonly ArtifactExplorerItem[] {
  if (selectedFolderId === null) {
    return allItems;
  }

  if (mode === "panel") {
    // selectedFolderId is a TypeBucket id like "images", "documents", etc.
    return allItems.filter(
      (item) => classifyContentType(item.contentType) === selectedFolderId,
    );
  }

  // Page mode: selectedFolderId is "convId:typeBucket"
  const colonIdx = selectedFolderId.indexOf(":");
  if (colonIdx === -1) {
    return allItems;
  }

  const convId = selectedFolderId.slice(0, colonIdx);
  const typeBucket = selectedFolderId.slice(colonIdx + 1);

  return allItems.filter(
    (item) =>
      item.conversationId === convId &&
      classifyContentType(item.contentType) === typeBucket,
  );
}

// ---------------------------------------------------------------------------
// Public component
// ---------------------------------------------------------------------------

export function ArtifactExplorer({
  artifacts,
  conversationId,
  groups,
  mode,
}: ArtifactExplorerProps) {
  const { t } = useTranslation();

  const {
    selectedFolderId,
    selectedFileId,
    expandedConversations,
    selectFolder,
    selectFile,
    toggleConversation,
  } = useArtifactExplorer();

  // ── Build normalized item list ──────────────────────────────────────────

  const allItems = useMemo((): readonly ArtifactExplorerItem[] => {
    if (mode === "panel") {
      const raw = artifacts ?? [];
      return raw.map(
        (a): ArtifactExplorerItem => ({
          id: a.id,
          name: a.name,
          contentType: a.contentType,
          size: a.size,
          conversationId: conversationId ?? undefined,
        }),
      );
    }

    // Page mode: flatten all conversation groups
    const groupList = groups ?? [];
    return groupList.flatMap((group) =>
      group.artifacts.map(
        (artifact): ArtifactExplorerItem => ({
          id: artifact.id,
          name: artifact.name,
          contentType: artifact.content_type,
          size: artifact.size,
          conversationId: group.conversation_id,
          conversationTitle: group.title ?? "Conversation",
          createdAt: artifact.created_at,
        }),
      ),
    );
  }, [mode, artifacts, conversationId, groups]);

  // ── Build folder structure ───────────────────────────────────────────────

  const typeFolders = useMemo(
    (): readonly FolderNode[] => groupArtifactsByType(allItems),
    [allItems],
  );

  const conversationNodes = useMemo(
    (): readonly ConversationNode[] =>
      mode === "page" ? groupByConversation(groups ?? []) : [],
    [mode, groups],
  );

  // ── Filter items for selected folder ────────────────────────────────────

  const visibleItems = useMemo(
    () => filterItemsForFolder(allItems, selectedFolderId, mode),
    [allItems, selectedFolderId, mode],
  );

  // ── Derive selected item + URL ───────────────────────────────────────────

  const selectedItem = useMemo(
    () => allItems.find((item) => item.id === selectedFileId) ?? null,
    [allItems, selectedFileId],
  );

  const selectedUrl = useMemo(
    () =>
      selectedItem
        ? buildArtifactUrl(selectedItem, mode === "panel" ? conversationId : null)
        : null,
    [selectedItem, mode, conversationId],
  );

  // ── Handlers ────────────────────────────────────────────────────────────

  const handlePreview = useCallback(
    (item: ArtifactExplorerItem) => {
      selectFile(item.id);
    },
    [selectFile],
  );

  const handleDownload = useCallback(
    (item: ArtifactExplorerItem) => {
      const url = buildArtifactUrl(item, mode === "panel" ? conversationId : null);
      if (url) {
        downloadFile(url, item.name);
      }
    },
    [mode, conversationId],
  );

  const handleDialogOpenChange = useCallback(
    (open: boolean) => {
      if (!open) selectFile(null);
    },
    [selectFile],
  );

  // ── Empty state ──────────────────────────────────────────────────────────

  if (allItems.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <EmptyState
          icon={FolderOpen}
          title={t("library.noArtifacts")}
          description={t("library.noArtifactsHint")}
        />
      </div>
    );
  }

  // ── Panel mode layout ────────────────────────────────────────────────────

  if (mode === "panel") {
    // Panel mode: sidebar + file list + dialog (no inline preview pane)
    const dialogArtifact = selectedItem
      ? {
          id: selectedItem.id,
          name: selectedItem.name,
          contentType: selectedItem.contentType,
          size: selectedItem.size,
        }
      : null;

    return (
      <div className="flex h-full divide-x divide-border">
        <div className="w-[120px] shrink-0 overflow-y-auto">
          <ExplorerSidebar
            mode="panel"
            folders={typeFolders}
            expandedConversations={expandedConversations}
            selectedFolderId={selectedFolderId}
            onSelectFolder={selectFolder}
            onToggleConversation={toggleConversation}
          />
        </div>
        <div className="flex-1 min-w-0">
          <ExplorerFileList
            items={visibleItems}
            selectedFileId={selectedFileId}
            conversationId={conversationId ?? undefined}
            onSelectFile={selectFile}
            onPreview={handlePreview}
            onDownload={handleDownload}
            mode="panel"
          />
        </div>
        <ArtifactPreviewDialog
          artifact={dialogArtifact}
          artifactUrl={selectedUrl}
          open={selectedFileId !== null}
          onOpenChange={handleDialogOpenChange}
        />
      </div>
    );
  }

  // ── Page mode layout ─────────────────────────────────────────────────────

  return (
    <div className="flex h-full divide-x divide-border">
      <div className="w-[200px] shrink-0 overflow-y-auto">
        <ExplorerSidebar
          mode="page"
          conversations={conversationNodes}
          expandedConversations={expandedConversations}
          selectedFolderId={selectedFolderId}
          onSelectFolder={selectFolder}
          onToggleConversation={toggleConversation}
        />
      </div>
      <div className="flex-1 min-w-0">
        <ExplorerFileList
          items={visibleItems}
          selectedFileId={selectedFileId}
          onSelectFile={selectFile}
          onPreview={handlePreview}
          onDownload={handleDownload}
          mode="page"
        />
      </div>
      <ExplorerPreviewPane
        item={selectedItem}
        artifactUrl={selectedUrl}
        onDownload={handleDownload}
        className="w-[340px] shrink-0 border-l border-border overflow-y-auto"
      />
    </div>
  );
}

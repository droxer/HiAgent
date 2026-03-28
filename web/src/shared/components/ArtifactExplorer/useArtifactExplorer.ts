"use client";

import { useState, useCallback } from "react";

// Re-export types so existing importers of this module are unaffected
export type {
  ArtifactExplorerItem,
  FolderNode,
  ConversationNode,
} from "./artifactExplorerUtils";

// Re-export pure functions so existing importers of this module are unaffected
export {
  groupByConversation,
} from "./artifactExplorerUtils";

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export interface ArtifactExplorerState {
  readonly selectedFolderId: string | null;
  readonly selectedFileId: string | null;
  readonly selectedIds: ReadonlySet<string>;
  readonly expandedConversations: ReadonlySet<string>;
  readonly selectFolder: (id: string | null) => void;
  readonly selectFile: (id: string | null) => void;
  readonly toggleConversation: (id: string) => void;
  readonly toggleSelection: (id: string) => void;
  readonly selectAll: (ids: readonly string[]) => void;
  readonly clearSelection: () => void;
}

export function useArtifactExplorer(): ArtifactExplorerState {
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<ReadonlySet<string>>(new Set());
  const [expandedConversations, setExpandedConversations] = useState<ReadonlySet<string>>(new Set());

  const selectFolder = useCallback((id: string | null): void => {
    setSelectedFolderId(id);
    setSelectedFileId(null);
  }, []);

  const selectFile = useCallback((id: string | null): void => {
    setSelectedFileId(id);
  }, []);

  const toggleConversation = useCallback((id: string): void => {
    setExpandedConversations((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const toggleSelection = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const selectAll = useCallback((ids: readonly string[]) => {
    setSelectedIds(new Set(ids));
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  return {
    selectedFolderId,
    selectedFileId,
    selectedIds,
    expandedConversations,
    selectFolder,
    selectFile,
    toggleConversation,
    toggleSelection,
    selectAll,
    clearSelection,
  };
}

"use client";

import { useCallback } from "react";
import { ChevronRight, ChevronDown, FolderOpen, Folder } from "lucide-react";
import { useTranslation } from "@/i18n";
import type { FolderNode, ConversationNode } from "./artifactExplorerUtils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ExplorerSidebarProps {
  // Panel mode
  folders?: readonly FolderNode[];
  // Page mode
  conversations?: readonly ConversationNode[];
  expandedConversations: ReadonlySet<string>;
  selectedFolderId: string | null;
  onSelectFolder: (id: string | null) => void;
  onToggleConversation: (id: string) => void;
  mode: "panel" | "page";
}

// ---------------------------------------------------------------------------
// Panel mode sidebar — flat list of type folders
// ---------------------------------------------------------------------------

interface PanelSidebarProps {
  folders: readonly FolderNode[];
  selectedFolderId: string | null;
  onSelectFolder: (id: string | null) => void;
}

function PanelSidebar({ folders, selectedFolderId, onSelectFolder }: PanelSidebarProps) {
  const { t } = useTranslation();

  const handleContainerKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLElement>) => {
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      e.preventDefault();
      const container = e.currentTarget;
      const buttons = Array.from(container.querySelectorAll<HTMLButtonElement>("button"));
      const current = document.activeElement as HTMLButtonElement;
      const idx = buttons.indexOf(current);
      if (idx === -1) {
        buttons[0]?.focus();
        return;
      }
      const next = e.key === "ArrowDown" ? buttons[idx + 1] : buttons[idx - 1];
      next?.focus();
    },
    [],
  );

  return (
    <nav
      aria-label={t("explorer.sidebarLabel")}
      className="flex flex-col gap-0.5 p-1.5"
      onKeyDown={handleContainerKeyDown}
    >
      {folders.map((folder) => {
        const isActive =
          folder.id === "all"
            ? selectedFolderId === null
            : selectedFolderId === folder.id;
        const FolderIcon = folder.id === "all" ? FolderOpen : folder.icon;

        return (
          <button
            key={folder.id}
            type="button"
            onClick={() => onSelectFolder(folder.id === "all" ? null : folder.id)}
            className={`flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-left text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
              isActive
                ? "bg-secondary text-foreground font-medium"
                : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
            }`}
            aria-current={isActive ? "page" : undefined}
          >
            <FolderIcon className="h-3.5 w-3.5 shrink-0" />
            <span className="flex-1 truncate">{t(folder.labelKey)}</span>
            {folder.count > 0 && (
              <span
                className={`shrink-0 rounded px-1 py-0.5 font-mono text-micro tabular-nums ${
                  isActive
                    ? "bg-primary/15 text-primary"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {folder.count}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
}

// ---------------------------------------------------------------------------
// Page mode sidebar — conversation tree with expandable sub-folders
// ---------------------------------------------------------------------------

interface PageSidebarProps {
  conversations: readonly ConversationNode[];
  expandedConversations: ReadonlySet<string>;
  selectedFolderId: string | null;
  onSelectFolder: (id: string | null) => void;
  onToggleConversation: (id: string) => void;
}

function PageSidebar({
  conversations,
  expandedConversations,
  selectedFolderId,
  onSelectFolder,
  onToggleConversation,
}: PageSidebarProps) {
  const { t } = useTranslation();

  const handleContainerKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLElement>) => {
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      e.preventDefault();
      const container = e.currentTarget;
      const buttons = Array.from(container.querySelectorAll<HTMLButtonElement>("button"));
      const current = document.activeElement as HTMLButtonElement;
      const idx = buttons.indexOf(current);
      if (idx === -1) {
        buttons[0]?.focus();
        return;
      }
      const next = e.key === "ArrowDown" ? buttons[idx + 1] : buttons[idx - 1];
      next?.focus();
    },
    [],
  );

  return (
    <nav
      aria-label={t("explorer.sidebarLabel")}
      className="flex flex-col gap-0.5 p-1.5"
      onKeyDown={handleContainerKeyDown}
    >
      {/* "All files" entry at the top */}
      <button
        type="button"
        onClick={() => onSelectFolder(null)}
        className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
          selectedFolderId === null
            ? "bg-secondary text-foreground font-medium"
            : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
        }`}
        aria-current={selectedFolderId === null ? "page" : undefined}
      >
        <FolderOpen className="h-4 w-4 shrink-0" />
        <span className="flex-1 truncate">{t("explorer.allFiles")}</span>
        <span
          className={`shrink-0 rounded px-1.5 py-0.5 text-xs font-mono tabular-nums ${
            selectedFolderId === null
              ? "bg-primary/15 text-primary"
              : "bg-muted text-muted-foreground"
          }`}
        >
          {conversations.reduce((sum, c) => sum + c.totalCount, 0)}
        </span>
      </button>

      <div className="my-1 border-t border-border" />

      {conversations.map((conversation) => {
        const isExpanded = expandedConversations.has(conversation.id);

        return (
          <div key={conversation.id} className="flex flex-col gap-0.5">
            {/* Conversation header row */}
            <button
              type="button"
              onClick={() => onToggleConversation(conversation.id)}
              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm text-muted-foreground transition-colors hover:bg-secondary/60 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-expanded={isExpanded}
            >
              {isExpanded ? (
                <ChevronDown className="h-3.5 w-3.5 shrink-0" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5 shrink-0" />
              )}
              <Folder className="h-4 w-4 shrink-0" />
              <span className="flex-1 truncate" title={conversation.title}>
                {conversation.title}
              </span>
              <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-xs font-mono tabular-nums text-muted-foreground">
                {conversation.totalCount}
              </span>
            </button>

            {/* Sub-folder list — only visible when expanded */}
            {isExpanded && conversation.subFolders.length > 0 && (
              <div className="ml-4 flex flex-col gap-0.5 border-l border-border pl-2">
                {conversation.subFolders.map((folder) => {
                  const subFolderId = `${conversation.id}:${folder.id}`;
                  const isActive = selectedFolderId === subFolderId;
                  const SubIcon = folder.icon;

                  return (
                    <button
                      key={folder.id}
                      type="button"
                      onClick={() => onSelectFolder(subFolderId)}
                      className={`flex w-full items-center gap-1.5 rounded-md px-2 py-1 text-left text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                        isActive
                          ? "bg-secondary text-foreground font-medium"
                          : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
                      }`}
                      aria-current={isActive ? "page" : undefined}
                    >
                      <SubIcon className="h-3.5 w-3.5 shrink-0" />
                      <span className="flex-1 truncate">{t(folder.labelKey)}</span>
                      <span
                        className={`shrink-0 rounded px-1 py-0.5 font-mono text-micro tabular-nums ${
                          isActive
                            ? "bg-primary/15 text-primary"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {folder.count}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
}

// ---------------------------------------------------------------------------
// Public component — delegates to panel or page variant
// ---------------------------------------------------------------------------

export function ExplorerSidebar({
  folders,
  conversations,
  expandedConversations,
  selectedFolderId,
  onSelectFolder,
  onToggleConversation,
  mode,
}: ExplorerSidebarProps) {
  if (mode === "panel") {
    return (
      <PanelSidebar
        folders={folders ?? []}
        selectedFolderId={selectedFolderId}
        onSelectFolder={onSelectFolder}
      />
    );
  }

  return (
    <PageSidebar
      conversations={conversations ?? []}
      expandedConversations={expandedConversations}
      selectedFolderId={selectedFolderId}
      onSelectFolder={onSelectFolder}
      onToggleConversation={onToggleConversation}
    />
  );
}

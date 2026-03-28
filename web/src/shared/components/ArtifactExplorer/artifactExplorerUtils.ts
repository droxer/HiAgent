import type { LibraryGroup } from "@/features/library/types";

export interface ArtifactExplorerItem {
  readonly id: string;
  readonly name: string;
  readonly contentType: string;
  readonly size: number;
  readonly conversationId?: string;
  readonly conversationTitle?: string;
  readonly createdAt?: string;
  readonly filePath?: string;
}

export interface FolderNode {
  readonly id: string;
  readonly name: string;
  readonly path: string;
  readonly isRoot: boolean;
  readonly subFolders: readonly FolderNode[];
  readonly items: readonly ArtifactExplorerItem[];
}

export interface ConversationNode {
  readonly id: string;
  readonly title: string;
  readonly createdAt: string;
  readonly rootFolder: FolderNode;
  readonly totalCount: number;
}

export function buildArtifactUrl(
  item: ArtifactExplorerItem,
  conversationId?: string | null,
): string | null {
  const convId = conversationId ?? item.conversationId;
  if (!convId) return null;
  return `/api/conversations/${convId}/artifacts/${item.id}`;
}

export function buildFileTree(
  items: readonly ArtifactExplorerItem[],
  rootId: string = "all",
): FolderNode {
  const root: FolderNode = { id: rootId, name: "/", path: "/", isRoot: true, subFolders: [], items: [] };
  const folderMap = new Map<string, FolderNode>([["/", root]]);

  for (const item of items) {
    const rawPath = item.filePath || item.name;
    const parts = rawPath.split("/").filter(Boolean);

    if (parts.length <= 1) {
      (root.items as ArtifactExplorerItem[]).push(item);
      continue;
    }

    let currentPath = "";
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      const prevPath = currentPath || "/";
      currentPath = currentPath ? `${currentPath}/${part}` : part;

      if (!folderMap.has(currentPath)) {
        const newFolder: FolderNode = {
          id: `${rootId}:${currentPath}`,
          name: part,
          path: currentPath,
          isRoot: false,
          subFolders: [],
          items: [],
        };
        folderMap.set(currentPath, newFolder);
        const parent = folderMap.get(prevPath)!;
        (parent.subFolders as FolderNode[]).push(newFolder);
      }
    }

    const parentFolder = folderMap.get(currentPath)!;
    (parentFolder.items as ArtifactExplorerItem[]).push(item);
  }

  return root;
}

export function groupByConversation(
  groups: readonly LibraryGroup[],
): readonly ConversationNode[] {
  return Object.freeze(
    groups.map((group): ConversationNode => {
      const items = Object.freeze(
        group.artifacts.map((a): ArtifactExplorerItem => ({
          id: a.id,
          name: a.name,
          contentType: a.content_type,
          size: a.size,
          conversationId: group.conversation_id,
          conversationTitle: group.title ?? "Conversation",
          createdAt: a.created_at,
          filePath: a.file_path || a.name,
        })),
      );

      return {
        id: group.conversation_id,
        title: group.title ?? "Conversation",
        createdAt: group.created_at,
        rootFolder: buildFileTree(items, group.conversation_id),
        totalCount: items.length,
      };
    }),
  );
}

import {
  FolderOpen,
  FileImage,
  FileText,
  FileCode,
  FileSpreadsheet,
  File,
  type LucideIcon,
} from "lucide-react";
import type { LibraryGroup } from "@/features/library/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ArtifactExplorerItem {
  readonly id: string;
  readonly name: string;
  readonly contentType: string;
  readonly size: number;
  readonly conversationId?: string;
  readonly conversationTitle?: string;
  readonly createdAt?: string;
}

export type FolderNodeId =
  | "all"
  | "images"
  | "documents"
  | "code"
  | "spreadsheets"
  | "other";

export interface FolderNode {
  readonly id: FolderNodeId;
  readonly labelKey: string;
  readonly icon: LucideIcon;
  readonly count: number;
  readonly items: readonly ArtifactExplorerItem[];
}

export interface ConversationNode {
  readonly id: string;
  readonly title: string;
  readonly createdAt: string;
  readonly subFolders: readonly FolderNode[];
  readonly totalCount: number;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

type TypeBucket = Exclude<FolderNodeId, "all">;

export const TYPE_FOLDER_META: ReadonlyArray<{
  readonly id: TypeBucket;
  readonly labelKey: string;
  readonly icon: LucideIcon;
}> = [
  { id: "images", labelKey: "explorer.images", icon: FileImage },
  { id: "documents", labelKey: "explorer.documents", icon: FileText },
  { id: "code", labelKey: "explorer.code", icon: FileCode },
  { id: "spreadsheets", labelKey: "explorer.spreadsheets", icon: FileSpreadsheet },
  { id: "other", labelKey: "explorer.other", icon: File },
] as const;

export function classifyContentType(contentType: string): TypeBucket {
  if (contentType.startsWith("image/")) return "images";

  if (
    contentType === "application/pdf" ||
    contentType.includes("wordprocessingml") ||
    contentType.includes("presentationml") ||
    contentType === "text/plain"
  )
    return "documents";

  if (
    contentType.startsWith("text/x-") ||
    contentType === "text/javascript" ||
    contentType === "application/json" ||
    contentType === "text/html"
  )
    return "code";

  if (contentType === "text/csv" || contentType.includes("spreadsheet"))
    return "spreadsheets";

  // Remaining text/* types go to documents (generic text)
  if (contentType.startsWith("text/")) return "documents";

  return "other";
}

// ---------------------------------------------------------------------------
// URL builder
// ---------------------------------------------------------------------------

export function buildArtifactUrl(
  item: ArtifactExplorerItem,
  conversationId?: string | null,
): string | null {
  const convId = conversationId ?? item.conversationId;
  if (!convId) return null;
  return `/api/conversations/${convId}/artifacts/${item.id}`;
}

// ---------------------------------------------------------------------------
// Pure functions
// ---------------------------------------------------------------------------

export function groupArtifactsByType(
  items: readonly ArtifactExplorerItem[],
): readonly FolderNode[] {
  // "all" folder always first
  const allFolder: FolderNode = {
    id: "all",
    labelKey: "explorer.allFiles",
    icon: FolderOpen,
    count: items.length,
    items,
  };

  // One FolderNode per type with count > 0, in fixed order — no mutation
  const typeFolders = TYPE_FOLDER_META
    .map((meta) => {
      const bucketItems = items.filter(
        (item) => classifyContentType(item.contentType) === meta.id,
      );
      return {
        ...meta,
        count: bucketItems.length,
        items: Object.freeze(bucketItems) as readonly ArtifactExplorerItem[],
      };
    })
    .filter((folder) => folder.count > 0);

  return Object.freeze([allFolder, ...typeFolders]);
}

export function groupByConversation(
  groups: readonly LibraryGroup[],
): readonly ConversationNode[] {
  return Object.freeze(
    groups.map((group): ConversationNode => {
      const items: readonly ArtifactExplorerItem[] = Object.freeze(
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

      // subFolders excludes the "all" folder — only type folders with count > 0
      const allFolders = groupArtifactsByType(items);
      const subFolders: readonly FolderNode[] = Object.freeze(
        allFolders.filter((f) => f.id !== "all"),
      );

      return {
        id: group.conversation_id,
        title: group.title ?? "Conversation",
        createdAt: group.created_at,
        subFolders,
        totalCount: items.length,
      };
    }),
  );
}

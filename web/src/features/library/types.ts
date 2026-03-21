export type ViewMode = "list" | "grid";

export interface LibraryArtifact {
  readonly id: string;
  readonly name: string;
  readonly content_type: string;
  readonly size: number;
  readonly created_at: string;
}

export interface LibraryGroup {
  readonly conversation_id: string;
  readonly title: string | null;
  readonly created_at: string;
  readonly artifacts: readonly LibraryArtifact[];
}

export interface LibraryResponse {
  readonly groups: readonly LibraryGroup[];
  readonly total: number;
}

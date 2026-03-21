import { API_BASE } from "@/shared/constants";

export interface Skill {
  readonly name: string;
  readonly description: string;
  readonly source_path: string;
  readonly source_type: "bundled" | "user" | "project";
  readonly instructions?: string;
  readonly enabled: boolean;
}

export interface SkillInstallParams {
  readonly url?: string;
  readonly source?: "git" | "url" | "registry";
  readonly name?: string;
  readonly skill_path?: string;
}

export interface RegistrySearchResult {
  readonly name: string;
  readonly description: string;
}

export async function fetchSkills(): Promise<readonly Skill[]> {
  const res = await fetch(`${API_BASE}/skills`);
  if (!res.ok) {
    throw new Error(`Failed to fetch skills: ${res.status}`);
  }
  const data = await res.json();
  return data.skills;
}

export async function fetchSkillDetail(name: string): Promise<Skill> {
  const res = await fetch(`${API_BASE}/skills/${encodeURIComponent(name)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch skill: ${res.status}`);
  }
  return res.json();
}

export async function installSkill(params: SkillInstallParams): Promise<Skill> {
  const res = await fetch(`${API_BASE}/skills/install`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Failed to install skill: ${detail}`);
  }
  return res.json();
}

export async function uninstallSkill(name: string): Promise<void> {
  const res = await fetch(
    `${API_BASE}/skills/${encodeURIComponent(name)}`,
    { method: "DELETE" },
  );
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Failed to uninstall skill: ${detail}`);
  }
}

export async function toggleSkill(
  name: string,
  enabled: boolean,
): Promise<{ name: string; enabled: boolean }> {
  const res = await fetch(
    `${API_BASE}/skills/${encodeURIComponent(name)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    },
  );
  if (!res.ok) {
    throw new Error(`Failed to toggle skill: ${res.status}`);
  }
  return res.json();
}

export async function uploadSkill(files: readonly File[]): Promise<Skill> {
  const formData = new FormData();
  for (const file of files) {
    // Use webkitRelativePath if available (folder upload), otherwise just name
    const filename = file.webkitRelativePath || file.name;
    formData.append("files", file, filename);
  }
  const res = await fetch(`${API_BASE}/skills/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Failed to upload skill: ${detail}`);
  }
  return res.json();
}

// ── File explorer types & functions ──

export interface FileTreeNode {
  readonly name: string;
  readonly path: string;
  readonly type: "file" | "directory";
  readonly children?: readonly FileTreeNode[];
}

export async function fetchSkillFiles(
  name: string,
): Promise<readonly FileTreeNode[]> {
  const res = await fetch(
    `${API_BASE}/skills/${encodeURIComponent(name)}/files`,
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch skill files: ${res.status}`);
  }
  return res.json();
}

export async function fetchSkillFileContent(
  name: string,
  path: string,
): Promise<string> {
  const res = await fetch(
    `${API_BASE}/skills/${encodeURIComponent(name)}/files/${encodeURIComponent(path)}`,
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch file content: ${res.status}`);
  }
  return res.text();
}

export async function searchRegistry(
  query: string,
): Promise<readonly RegistrySearchResult[]> {
  const res = await fetch(
    `${API_BASE}/skills/registry/search?q=${encodeURIComponent(query)}`,
  );
  if (!res.ok) {
    throw new Error(`Failed to search registry: ${res.status}`);
  }
  const data = await res.json();
  return data.results;
}

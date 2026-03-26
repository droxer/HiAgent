import { Package, Globe, FolderGit2 } from "lucide-react";

export const SOURCE_STYLE = {
  bundled: { icon: Package, className: "bg-secondary text-muted-foreground" },
  user: { icon: Globe, className: "bg-accent-emerald/10 text-accent-emerald" },
  project: { icon: FolderGit2, className: "bg-accent-purple/10 text-accent-purple" },
} as const;

export const SOURCE_LABEL_KEY: Record<string, string> = {
  bundled: "skills.source.bundled",
  user: "skills.source.user",
  project: "skills.source.project",
};

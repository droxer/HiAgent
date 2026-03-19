"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  fetchSkillFiles,
  fetchSkillFileContent,
  type FileTreeNode,
} from "../api/skills-api";

interface UseSkillFilesResult {
  readonly fileTree: readonly FileTreeNode[];
  readonly selectedPath: string | null;
  readonly fileContent: string | null;
  readonly isLoadingTree: boolean;
  readonly isLoadingContent: boolean;
  readonly selectFile: (path: string) => void;
}

export function useSkillFiles(skillName: string): UseSkillFilesResult {
  const [fileTree, setFileTree] = useState<readonly FileTreeNode[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [isLoadingTree, setIsLoadingTree] = useState(true);
  const [isLoadingContent, setIsLoadingContent] = useState(false);

  // Cache fetched file contents to avoid re-fetching
  const contentCache = useRef(new Map<string, string>());

  // Fetch tree on mount
  useEffect(() => {
    let cancelled = false;
    contentCache.current = new Map();

    setIsLoadingTree(true);
    fetchSkillFiles(skillName)
      .then((tree) => {
        if (cancelled) return;
        setFileTree(tree);
        setIsLoadingTree(false);

        // Auto-select SKILL.md if present
        const skillMd = findFile(tree, "SKILL.md");
        if (skillMd) {
          setSelectedPath(skillMd);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFileTree([]);
          setIsLoadingTree(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [skillName]);

  // Fetch content when selectedPath changes
  useEffect(() => {
    if (selectedPath === null) {
      setFileContent(null);
      return;
    }

    const cached = contentCache.current.get(selectedPath);
    if (cached !== undefined) {
      setFileContent(cached);
      return;
    }

    let cancelled = false;
    setIsLoadingContent(true);

    fetchSkillFileContent(skillName, selectedPath)
      .then((content) => {
        if (cancelled) return;
        contentCache.current.set(selectedPath, content);
        setFileContent(content);
        setIsLoadingContent(false);
      })
      .catch(() => {
        if (!cancelled) {
          setFileContent(null);
          setIsLoadingContent(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [skillName, selectedPath]);

  const selectFile = useCallback((path: string) => {
    setSelectedPath(path);
  }, []);

  return {
    fileTree,
    selectedPath,
    fileContent,
    isLoadingTree,
    isLoadingContent,
    selectFile,
  };
}

/** Find the path of the first file with a given name in the tree. */
function findFile(
  nodes: readonly FileTreeNode[],
  name: string,
): string | null {
  for (const node of nodes) {
    if (node.type === "file" && node.name === name) {
      return node.path;
    }
    if (node.children) {
      const found = findFile(node.children, name);
      if (found) return found;
    }
  }
  return null;
}

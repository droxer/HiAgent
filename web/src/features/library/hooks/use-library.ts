"use client";

import { useState, useEffect, useCallback } from "react";
import type { LibraryGroup } from "../types";
import { fetchLibrary } from "../api/library-api";

const PAGE_SIZE = 20;

export function useLibrary() {
  const [groups, setGroups] = useState<readonly LibraryGroup[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [filter, setFilter] = useState("");

  const load = useCallback(async (currentOffset: number, append: boolean) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchLibrary(PAGE_SIZE, currentOffset);
      setGroups((prev) =>
        append ? [...prev, ...data.groups] : data.groups,
      );
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load library");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load(0, false);
  }, [load]);

  const loadMore = useCallback(() => {
    const nextOffset = offset + PAGE_SIZE;
    setOffset(nextOffset);
    load(nextOffset, true);
  }, [offset, load]);

  const hasMore = groups.length < total;

  const filtered = filter
    ? groups
        .map((g) => {
          const matchTitle = g.title
            ?.toLowerCase()
            .includes(filter.toLowerCase());
          const matchingArtifacts = g.artifacts.filter((a) =>
            a.name.toLowerCase().includes(filter.toLowerCase()),
          );
          if (matchTitle) return g;
          if (matchingArtifacts.length > 0)
            return { ...g, artifacts: matchingArtifacts };
          return null;
        })
        .filter((g): g is LibraryGroup => g !== null)
    : groups;

  return {
    groups: filtered,
    total,
    isLoading,
    error,
    filter,
    setFilter,
    loadMore,
    hasMore,
  };
}

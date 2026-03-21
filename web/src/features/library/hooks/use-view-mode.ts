"use client";

import { useState, useEffect, useCallback } from "react";
import type { ViewMode } from "../types";

const STORAGE_KEY = "hiagent-library-view-mode";

export function useViewMode() {
  const [viewMode, setViewModeState] = useState<ViewMode>("grid");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "list" || stored === "grid") {
      setViewModeState(stored);
    }
  }, []);

  const setViewMode = useCallback((mode: ViewMode) => {
    localStorage.setItem(STORAGE_KEY, mode);
    setViewModeState(mode);
  }, []);

  return { viewMode, setViewMode } as const;
}

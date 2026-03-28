"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { FolderOpen } from "lucide-react";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import { SearchInput } from "@/shared/components/SearchInput";
import { Button } from "@/shared/components/ui/button";
import { ArtifactExplorer } from "@/shared/components/ArtifactExplorer";
import { useTranslation } from "@/i18n";
import { useLibrary } from "../hooks/use-library";

function GroupSkeleton() {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 px-2 py-1.5">
        <div className="h-4 w-4 skeleton-shimmer rounded" />
        <div className="h-4 w-48 skeleton-shimmer rounded" />
        <div className="flex-1" />
        <div className="h-4 w-20 skeleton-shimmer rounded" />
      </div>
      <div className="ml-6 space-y-1.5">
        <div className="h-[58px] rounded-lg skeleton-shimmer" />
        <div className="h-[58px] rounded-lg skeleton-shimmer" />
      </div>
    </div>
  );
}

export function LibraryPage() {
  const { t } = useTranslation();
  const { groups, isLoading, error, filter, setFilter, loadMore, hasMore } =
    useLibrary();
  const [dismissedError, setDismissedError] = useState<string | null>(null);

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Header */}
      <motion.div
        className="shrink-0 border-b border-border px-6 py-5"
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.12, ease: "easeOut" }}
      >
        <div className="mx-auto flex max-w-5xl items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary">
              <FolderOpen className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight text-foreground">
                {t("library.title")}
              </h1>
              <p className="text-xs text-muted-foreground">
                {t("library.subtitle")}
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Content */}
      <div className="flex flex-1 flex-col overflow-hidden px-4 py-6 sm:px-6">
        <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-5 overflow-hidden">
          {/* Error */}
          {error && error !== dismissedError && (
            <ErrorBanner message={error} onDismiss={() => setDismissedError(error)} />
          )}

          {/* Filter bar */}
          {groups.length > 0 || filter ? (
            <div className="flex shrink-0 items-center gap-3">
              <h2 className="text-base font-medium text-muted-foreground">
                {t("library.title")}
              </h2>
              <div className="flex-1" />
              <SearchInput
                value={filter}
                onChange={setFilter}
                placeholder={t("library.filterPlaceholder")}
                clearLabel={t("library.clearFilter")}
              />
            </div>
          ) : null}

          {/* Loading state */}
          {isLoading && groups.length === 0 ? (
            <div className="space-y-6">
              <GroupSkeleton />
              <GroupSkeleton />
              <GroupSkeleton />
            </div>
          ) : (
            <div className="flex-1 overflow-hidden">
              <ArtifactExplorer mode="page" groups={groups} />
            </div>
          )}

          {/* Load more */}
          {hasMore && !isLoading && (
            <div className="flex shrink-0 justify-center pt-2">
              <Button variant="outline" size="sm" onClick={loadMore}>
                {t("library.loadMore")}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

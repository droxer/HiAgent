"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Wand, Plus, Package, Search, X } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/components/ui/alert-dialog";
import { SkillCard } from "./SkillCard";
import { useSkillsCache } from "../hooks/use-skills-cache";
import { normalizeSkillName } from "../lib/normalize-skill-name";
import {
  installSkill,
  uninstallSkill,
  type SkillInstallParams,
} from "../api/skills-api";
import { useTranslation } from "@/i18n";

/* ── animation variants ── */
const listContainer = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.06, delayChildren: 0.15 },
  },
};

const listItem = {
  hidden: { opacity: 0, y: 6 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.25, ease: "easeOut" as const },
  },
};

/* ── skeleton ── */
function SkillSkeleton() {
  return (
    <div className="flex gap-3.5 rounded-lg border border-border bg-card px-4 py-3.5 shadow-sm">
      <div className="h-9 w-9 shrink-0 rounded-lg bg-muted-foreground/10 animate-shimmer" />
      <div className="flex-1 space-y-2.5 pt-0.5">
        <div className="flex items-center gap-2">
          <div className="h-3.5 w-28 rounded bg-muted-foreground/10 animate-shimmer" />
          <div className="h-4 w-16 rounded bg-muted-foreground/8 animate-shimmer" />
        </div>
        <div className="h-3 w-full max-w-xs rounded bg-muted-foreground/8 animate-shimmer" />
        <div className="h-3 w-20 rounded bg-muted-foreground/6 animate-shimmer" />
      </div>
    </div>
  );
}

type InstallSource = "git" | "url";

export function SkillsPage() {
  const { t } = useTranslation();
  const { getAllSkills, isLoading } = useSkillsCache();
  const skills = getAllSkills();

  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

  // Install form state
  const [showForm, setShowForm] = useState(false);
  const [installSource, setInstallSource] = useState<InstallSource>("git");
  const [formUrl, setFormUrl] = useState("");
  const [formSkillPath, setFormSkillPath] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Delete confirmation
  const [skillToDelete, setSkillToDelete] = useState<string | null>(null);

  const resetForm = () => {
    setFormUrl("");
    setFormSkillPath("");
    setShowForm(false);
  };

  const handleInstall = async () => {
    if (!formUrl.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const params: SkillInstallParams = {
        source: installSource,
        url: formUrl.trim(),
        skill_path: formSkillPath.trim() || undefined,
      };
      await installSkill(params);
      resetForm();
      // Cache will refresh on next render cycle via useSkillsCache
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to install skill");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = useCallback(async () => {
    if (!skillToDelete) return;
    setError(null);
    try {
      await uninstallSkill(skillToDelete);
      setSkillToDelete(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to uninstall skill",
      );
    }
  }, [skillToDelete]);

  const bundledSkills = skills.filter((s) => s.source_type === "bundled");
  const installedSkills = skills.filter((s) => s.source_type !== "bundled");

  const filtered = filter
    ? skills.filter(
        (s) =>
          s.name.toLowerCase().includes(filter.toLowerCase()) ||
          s.description?.toLowerCase().includes(filter.toLowerCase()),
      )
    : null;

  const displaySkills = filtered ?? skills;

  return (
    <div className="flex h-full flex-col bg-background">
      {/* ── Header ── */}
      <motion.div
        className="shrink-0 border-b border-border px-6 py-5"
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
      >
        <div className="mx-auto flex max-w-2xl items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary">
              <Wand className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <h1 className="text-base font-semibold tracking-tight text-foreground">
                {t("skills.title")}
              </h1>
              <p className="text-xs text-muted-foreground">
                {t("skills.subtitle")}
              </p>
            </div>
          </div>
          {skills.length > 0 && (
            <div className="flex items-center gap-1.5 rounded-md bg-secondary px-2.5 py-1">
              <Package className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground">
                {t("skills.builtIn", { count: bundledSkills.length })}
                {installedSkills.length > 0 && t("skills.installed", { count: installedSkills.length })}
              </span>
            </div>
          )}
        </div>
      </motion.div>

      {/* ── Content ── */}
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        <div className="mx-auto max-w-2xl space-y-5">
          {/* Error banner */}
          {error && (
            <motion.div
              className="flex items-center gap-2 rounded-md border border-destructive/20 bg-destructive/5 px-4 py-2.5"
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-destructive" />
              <p className="flex-1 text-sm text-destructive">{error}</p>
              <button
                type="button"
                onClick={() => setError(null)}
                className="rounded-sm p-0.5 text-destructive/60 transition-colors hover:text-destructive"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </motion.div>
          )}

          {/* Section header with search + install */}
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-medium text-muted-foreground">
              {t("skills.agentSkills")}
            </h2>
            <div className="flex-1" />
            {skills.length > 3 && (
              <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-2.5 py-1.5">
                <Search className="h-3.5 w-3.5 text-muted-foreground-dim" />
                <input
                  type="text"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  placeholder={t("skills.filterPlaceholder")}
                  className="w-32 bg-transparent text-xs text-foreground placeholder:text-muted-foreground-dim outline-none"
                />
                {filter && (
                  <button
                    type="button"
                    onClick={() => setFilter("")}
                    className="rounded-sm p-0.5 text-muted-foreground-dim hover:text-muted-foreground"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
            )}
            {!showForm && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowForm(true)}
              >
                <Plus className="mr-1.5 h-3.5 w-3.5" />
                {t("skills.installSkill")}
              </Button>
            )}
          </div>

          {/* ── Skill list ── */}
          {isLoading && skills.length === 0 ? (
            <div className="space-y-3">
              <SkillSkeleton />
              <SkillSkeleton />
              <SkillSkeleton />
            </div>
          ) : displaySkills.length === 0 && filter ? (
            <motion.div
              className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border py-12"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.2 }}
            >
              <Search className="h-5 w-5 text-muted-foreground-dim" />
              <p className="text-sm text-muted-foreground">
                {t("skills.noSkillsMatching", { filter })}
              </p>
            </motion.div>
          ) : skills.length === 0 ? (
            <motion.div
              className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border py-14"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-secondary">
                <Wand className="h-5 w-5 text-muted-foreground-dim" />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-foreground">
                  {t("skills.noSkillsAvailable")}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {t("skills.noSkillsHint")}
                </p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              className="space-y-3"
              variants={listContainer}
              initial="hidden"
              animate="show"
            >
              {displaySkills.map((skill) => (
                <motion.div key={skill.name} variants={listItem}>
                  <SkillCard
                    skill={skill}
                    onDelete={setSkillToDelete}
                  />
                </motion.div>
              ))}
            </motion.div>
          )}

          {/* ── Install form ── */}
          {showForm && (
            <motion.div
              className="space-y-4 rounded-lg border border-border bg-card p-5"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
            >
              <h3 className="text-sm font-semibold text-foreground">
                {t("skills.installFormTitle")}
              </h3>

              {/* Source toggle */}
              <div className="space-y-1.5">
                <Label className="text-xs">{t("skills.source")}</Label>
                <div className="flex gap-1 rounded-lg bg-secondary p-1">
                  {(["git", "url"] as const).map((src) => (
                    <button
                      key={src}
                      type="button"
                      onClick={() => setInstallSource(src)}
                      className={`flex-1 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                        installSource === src
                          ? "bg-background text-foreground shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {src === "git" ? t("skills.gitRepo") : t("skills.url")}
                    </button>
                  ))}
                </div>
              </div>

              {/* URL field */}
              <div className="space-y-1.5">
                <Label htmlFor="skill-url" className="text-xs">
                  {installSource === "git" ? t("skills.repoUrl") : t("skills.skillUrl")}
                </Label>
                <Input
                  id="skill-url"
                  placeholder={
                    installSource === "git"
                      ? t("skills.repoPlaceholder")
                      : t("skills.urlPlaceholder")
                  }
                  value={formUrl}
                  onChange={(e) => setFormUrl(e.target.value)}
                  className="font-mono"
                />
              </div>

              {/* Skill path (git only) */}
              {installSource === "git" && (
                <div className="space-y-1.5">
                  <Label htmlFor="skill-path" className="text-xs">
                    {t("skills.skillPath")}{" "}
                    <span className="text-muted-foreground">{t("skills.optional")}</span>
                  </Label>
                  <Input
                    id="skill-path"
                    placeholder={t("skills.skillPathPlaceholder")}
                    value={formSkillPath}
                    onChange={(e) => setFormSkillPath(e.target.value)}
                    className="font-mono"
                  />
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end gap-2 pt-1">
                <Button variant="ghost" size="sm" onClick={resetForm}>
                  {t("skills.cancel")}
                </Button>
                <Button
                  size="sm"
                  onClick={handleInstall}
                  disabled={submitting || !formUrl.trim()}
                >
                  {submitting && (
                    <span className="mr-1.5 inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  )}
                  {t("skills.install")}
                </Button>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* ── Delete confirmation ── */}
      <AlertDialog
        open={skillToDelete !== null}
        onOpenChange={(isOpen) => {
          if (!isOpen) setSkillToDelete(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("skills.uninstallTitle")}</AlertDialogTitle>
            <AlertDialogDescription>
              {t("skills.uninstallDesc", { name: skillToDelete ? normalizeSkillName(skillToDelete) : "" })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t("skills.cancel")}</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-primary-foreground hover:bg-destructive/90"
            >
              {t("skills.uninstall")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

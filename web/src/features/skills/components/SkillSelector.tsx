"use client";

import { useState } from "react";
import { Wand, X, Search } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Popover, PopoverTrigger, PopoverContent } from "@/shared/components/ui/popover";
import { Badge } from "@/shared/components/ui/badge";
import { cn } from "@/shared/lib/utils";
import { useTranslation } from "@/i18n";
import { useSkillsCache } from "../hooks/use-skills-cache";
import { normalizeSkillName } from "../lib/normalize-skill-name";

interface SkillSelectorProps {
  readonly selectedSkill: string | null;
  readonly onSelect: (skillName: string | null) => void;
  /** Button size variant — "sm" for WelcomeScreen, "xs" for ChatInput */
  readonly buttonSize?: "icon-xs" | "icon-sm";
}

export function SkillSelector({
  selectedSkill,
  onSelect,
  buttonSize = "icon-xs",
}: SkillSelectorProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState("");

  const { getAllSkills } = useSkillsCache();
  const skills = getAllSkills();

  const filtered = filter
    ? skills.filter(
        (s) =>
          s.name.toLowerCase().includes(filter.toLowerCase()) ||
          s.description?.toLowerCase().includes(filter.toLowerCase()),
      )
    : skills;

  const handleSelect = (name: string) => {
    if (selectedSkill === name) {
      onSelect(null);
    } else {
      onSelect(name);
    }
    setOpen(false);
    setFilter("");
  };

  return (
    <>
      {/* Selected skill chip */}
      {selectedSkill && (
        <Badge
          variant="outline"
          className="gap-1.5 border-accent-purple/25 bg-accent-purple/[0.06] pr-1 text-xs text-foreground"
        >
          <Wand className="h-3 w-3 text-accent-purple" />
          {normalizeSkillName(selectedSkill)}
          <button
            type="button"
            onClick={() => onSelect(null)}
            aria-label={t("skills.selector.remove", { name: normalizeSkillName(selectedSkill) })}
            className="ml-0.5 rounded-full p-0.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
          >
            <X className="h-2.5 w-2.5" />
          </button>
        </Badge>
      )}

      {/* Trigger button + popover */}
      <Popover open={open} onOpenChange={(v) => { setOpen(v); if (!v) setFilter(""); }}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size={buttonSize}
            aria-label={t("skills.selector.select")}
            className={cn(
              "text-muted-foreground-dim hover:bg-secondary hover:text-muted-foreground",
              selectedSkill && "text-accent-purple",
            )}
          >
            <Wand className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent
          side="top"
          align="start"
          className="w-[min(20rem,calc(100vw-2rem))] overflow-hidden rounded-xl border border-border bg-popover p-0"
          style={{ boxShadow: "var(--shadow-elevated)" }}
        >
          {/* Header */}
          <div className="flex items-center gap-2 border-b border-border px-3 py-2.5">
            <Wand className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs font-semibold tracking-wide text-foreground">
              {t("skills.selector.title")}
            </span>
          </div>

          {/* Search filter */}
          {skills.length > 4 && (
            <div className="border-b border-border px-3 py-2">
              <div className="flex items-center gap-2 rounded-md border border-border bg-background px-2.5 py-1.5">
                <Search className="h-3.5 w-3.5 text-muted-foreground-dim" />
                <input
                  type="text"
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  placeholder={t("skills.selector.search")}
                  className="flex-1 bg-transparent text-xs text-foreground placeholder:text-placeholder outline-none"
                />
              </div>
            </div>
          )}

          {/* Skill list */}
          <div className="max-h-64 overflow-y-auto p-1.5">
            {filtered.length === 0 ? (
              <div className="px-3 py-6 text-center text-xs text-muted-foreground">
                {skills.length === 0
                  ? t("skills.selector.noSkills")
                  : t("skills.selector.noMatching")}
              </div>
            ) : (
              filtered.map((skill) => {
                const isSelected = selectedSkill === skill.name;
                return (
                  <button
                    key={skill.name}
                    type="button"
                    onClick={() => handleSelect(skill.name)}
                    className={cn(
                      "group flex w-full items-center gap-3 rounded-md px-2.5 py-2 text-left transition-colors",
                      "hover:bg-secondary/60",
                      "focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
                      isSelected && "bg-accent-purple/[0.06]",
                    )}
                  >
                    {/* Radio indicator */}
                    <div
                      className={cn(
                        "flex h-4 w-4 shrink-0 items-center justify-center rounded-full border transition-all",
                        isSelected
                          ? "border-accent-purple bg-accent-purple"
                          : "border-border group-hover:border-muted-foreground/40",
                      )}
                    >
                      {isSelected && (
                        <div className="h-1.5 w-1.5 rounded-full bg-primary-foreground" />
                      )}
                    </div>

                    {/* Skill info */}
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium text-foreground">
                        {normalizeSkillName(skill.name)}
                      </div>
                      {skill.description && (
                        <div className="mt-0.5 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
                          {skill.description}
                        </div>
                      )}
                    </div>

                    {/* Source type badge */}
                    <span
                      className={cn(
                        "shrink-0 rounded px-1.5 py-0.5 text-[0.625rem] font-medium",
                        skill.source_type === "bundled" &&
                          "bg-secondary text-muted-foreground",
                        skill.source_type === "user" &&
                          "bg-accent-emerald/10 text-accent-emerald",
                        skill.source_type === "project" &&
                          "bg-accent-purple/10 text-accent-purple",
                      )}
                    >
                      {skill.source_type === "bundled"
                        ? t("skills.source.bundled")
                        : skill.source_type === "user"
                          ? t("skills.source.user")
                          : t("skills.source.project")}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </PopoverContent>
      </Popover>
    </>
  );
}

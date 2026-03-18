"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun, Monitor } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { useTranslation } from "@/i18n";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/shared/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";

const THEME_OPTIONS = [
  { value: "light", icon: Sun, labelKey: "theme.light" },
  { value: "dark", icon: Moon, labelKey: "theme.dark" },
  { value: "system", icon: Monitor, labelKey: "theme.system" },
] as const;

const TRIGGER_ICON: Record<string, typeof Moon> = {
  dark: Moon,
  light: Sun,
  system: Monitor,
};

interface ThemeToggleProps {
  readonly collapsed?: boolean;
}

export function ThemeToggle({ collapsed = false }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme();
  const { t } = useTranslation();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className={collapsed ? "h-8 w-8" : "h-8"} />;
  }

  const current = theme ?? "dark";
  const Icon = TRIGGER_ICON[current] ?? Moon;
  const currentOption = THEME_OPTIONS.find((o) => o.value === current);
  const currentLabel = currentOption ? t(currentOption.labelKey) : t("theme.toggle");

  const trigger = collapsed ? (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          className="text-muted-foreground transition-colors duration-150 hover:text-foreground hover:bg-sidebar-hover"
        >
          <Icon className="h-3.5 w-3.5" />
          <span className="sr-only">{t("theme.toggle")}</span>
        </Button>
      </TooltipTrigger>
      <TooltipContent side="right">{currentLabel}</TooltipContent>
    </Tooltip>
  ) : (
    <Button
      variant="ghost"
      className="w-full justify-start gap-2.5 text-sm text-muted-foreground transition-colors duration-150 hover:text-foreground hover:bg-sidebar-hover"
      size="sm"
    >
      <Icon className="h-4 w-4" />
      {currentLabel}
    </Button>
  );

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        {trigger}
      </DropdownMenuTrigger>
      <DropdownMenuContent
        side={collapsed ? "right" : "top"}
        align="start"
        className="min-w-[7rem] rounded-lg border-border bg-popover shadow-elevated"
      >
        <DropdownMenuRadioGroup value={current} onValueChange={setTheme}>
          {THEME_OPTIONS.map(({ value, icon: ItemIcon, labelKey }) => (
            <DropdownMenuRadioItem
              key={value}
              value={value}
              className="gap-2 rounded-md text-xs"
            >
              <ItemIcon className="h-3.5 w-3.5 text-muted-foreground" />
              {t(labelKey)}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

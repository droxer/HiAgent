"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun, Monitor } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";

const THEME_OPTIONS = [
  { value: "light", icon: Sun, label: "Light" },
  { value: "dark", icon: Moon, label: "Dark" },
  { value: "system", icon: Monitor, label: "System" },
] as const;

const TRIGGER_ICON: Record<string, typeof Moon> = {
  dark: Moon,
  light: Sun,
  system: Monitor,
};

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="h-9 w-9" />;
  }

  const current = theme ?? "dark";
  const Icon = TRIGGER_ICON[current] ?? Moon;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 text-muted-foreground transition-colors duration-150 hover:text-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
        >
          <Icon className="h-3.5 w-3.5" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="min-w-[7rem] rounded-xl border-border bg-card/90 shadow-elevated backdrop-blur-xl"
      >
        <DropdownMenuRadioGroup value={current} onValueChange={setTheme}>
          {THEME_OPTIONS.map(({ value, icon: ItemIcon, label }) => (
            <DropdownMenuRadioItem
              key={value}
              value={value}
              className="gap-2 rounded-lg text-xs"
            >
              <ItemIcon className="h-3.5 w-3.5 text-muted-foreground" />
              {label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

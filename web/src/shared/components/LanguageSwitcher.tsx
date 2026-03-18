"use client";

import { Globe } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
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
import { useTranslation, LOCALES, LOCALE_LABELS, type Locale } from "@/i18n";

interface LanguageSwitcherProps {
  readonly collapsed?: boolean;
}

export function LanguageSwitcher({ collapsed = false }: LanguageSwitcherProps) {
  const { locale, setLocale } = useTranslation();

  const trigger = collapsed ? (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          className="text-muted-foreground transition-colors duration-150 hover:text-foreground hover:bg-sidebar-hover"
        >
          <Globe className="h-3.5 w-3.5" />
          <span className="sr-only">{LOCALE_LABELS[locale]}</span>
        </Button>
      </TooltipTrigger>
      <TooltipContent side="right">{LOCALE_LABELS[locale]}</TooltipContent>
    </Tooltip>
  ) : (
    <Button
      variant="ghost"
      className="w-full justify-start gap-2.5 text-sm text-muted-foreground transition-colors duration-150 hover:text-foreground hover:bg-sidebar-hover"
      size="sm"
    >
      <Globe className="h-4 w-4" />
      {LOCALE_LABELS[locale]}
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
        <DropdownMenuRadioGroup value={locale} onValueChange={(v) => setLocale(v as Locale)}>
          {LOCALES.map((loc) => (
            <DropdownMenuRadioItem
              key={loc}
              value={loc}
              className="gap-2 rounded-md text-xs"
            >
              {LOCALE_LABELS[loc]}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

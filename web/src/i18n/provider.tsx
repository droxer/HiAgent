"use client";

import { useState, useCallback, useEffect, useMemo, type ReactNode } from "react";
import { I18nContext, type I18nContextValue } from "./context";
import type { Locale, TranslationDict, TranslationParams } from "./types";
import { DEFAULT_LOCALE, COOKIE_NAME, LOCALES } from "./types";

function readLocale(): Locale {
  // 1. Cookie
  if (typeof document !== "undefined") {
    const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${COOKIE_NAME}=([^;]*)`));
    if (match) {
      const val = match[1] as Locale;
      if (LOCALES.includes(val)) return val;
    }
  }

  // 2. localStorage
  if (typeof localStorage !== "undefined") {
    try {
      const stored = localStorage.getItem(COOKIE_NAME) as Locale | null;
      if (stored && LOCALES.includes(stored)) return stored;
    } catch {
      // SSR or access denied
    }
  }

  // 3. navigator.language
  if (typeof navigator !== "undefined") {
    const lang = navigator.language;
    if (lang.startsWith("zh")) {
      if (lang === "zh-TW" || lang === "zh-HK" || lang.includes("Hant")) {
        return "zh-TW";
      }
      return "zh-CN";
    }
  }

  return DEFAULT_LOCALE;
}

function persistLocale(locale: Locale): void {
  // Cookie — 1 year, SameSite=Lax
  document.cookie = `${COOKIE_NAME}=${locale};path=/;max-age=31536000;SameSite=Lax`;
  // localStorage fallback
  try {
    localStorage.setItem(COOKIE_NAME, locale);
  } catch {
    // quota exceeded or access denied
  }
}

// Cache loaded dictionaries
const dictCache = new Map<Locale, TranslationDict>();

async function loadDict(locale: Locale): Promise<TranslationDict> {
  const cached = dictCache.get(locale);
  if (cached) return cached;

  let dict: TranslationDict;
  if (locale === "zh-TW") {
    dict = (await import("./locales/zh-TW.json")).default as TranslationDict;
  } else if (locale === "zh-CN") {
    dict = (await import("./locales/zh-CN.json")).default as TranslationDict;
  } else {
    dict = (await import("./locales/en.json")).default as TranslationDict;
  }
  dictCache.set(locale, dict);
  return dict;
}

function interpolate(template: string, params: TranslationParams): string {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => {
    const val = params[key];
    return val !== undefined ? String(val) : `{${key}}`;
  });
}

interface I18nProviderProps {
  readonly children: ReactNode;
}

export function I18nProvider({ children }: I18nProviderProps) {
  const [locale, setLocaleState] = useState<Locale>(DEFAULT_LOCALE);
  const [dict, setDict] = useState<TranslationDict>({});
  const [ready, setReady] = useState(false);

  // Initialise locale from persisted source
  useEffect(() => {
    const detected = readLocale();
    setLocaleState(detected);
    loadDict(detected).then((d) => {
      setDict(d);
      setReady(true);
    });
  }, []);

  // Update lang attribute
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    persistLocale(next);
    loadDict(next).then(setDict);
  }, []);

  const t = useCallback(
    (key: string, params?: TranslationParams): string => {
      const value = dict[key];
      if (typeof value !== "string") return key;
      return params ? interpolate(value, params) : value;
    },
    [dict],
  );

  const tArray = useCallback(
    (key: string): readonly string[] => {
      const value = dict[key];
      if (Array.isArray(value)) return value;
      if (typeof value === "string") return [value];
      return [key];
    },
    [dict],
  );

  const contextValue: I18nContextValue = useMemo(
    () => ({ locale, setLocale, t, tArray }),
    [locale, setLocale, t, tArray],
  );

  // Render children immediately — `t()` falls back to keys before dict loads
  // This avoids a blank flash. The `ready` flag can be used later if needed.
  void ready;

  return (
    <I18nContext.Provider value={contextValue}>
      {children}
    </I18nContext.Provider>
  );
}

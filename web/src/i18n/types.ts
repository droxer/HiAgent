export type Locale = "en" | "zh-CN";

export const DEFAULT_LOCALE: Locale = "en";

export const LOCALES: readonly Locale[] = ["en", "zh-CN"] as const;

export const LOCALE_LABELS: Record<Locale, string> = {
  en: "English",
  "zh-CN": "中文",
};

export const COOKIE_NAME = "hiagent-locale";

export type TranslationParams = Record<string, string | number>;

export type TranslationDict = Record<string, string | string[]>;

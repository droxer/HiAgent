"use client";

import { createContext } from "react";
import type { Locale, TranslationParams } from "./types";
import { DEFAULT_LOCALE } from "./types";

export interface I18nContextValue {
  readonly locale: Locale;
  readonly setLocale: (locale: Locale) => void;
  readonly t: (key: string, params?: TranslationParams) => string;
  readonly tArray: (key: string) => readonly string[];
}

const noop = () => {};

export const I18nContext = createContext<I18nContextValue>({
  locale: DEFAULT_LOCALE,
  setLocale: noop,
  t: (key: string) => key,
  tArray: (key: string) => [key],
});

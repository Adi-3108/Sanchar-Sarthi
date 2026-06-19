"use client";

import { languageOptions } from "@/lib/i18n";
import { useLanguage } from "@/components/LanguageContext";

/**
 * Dropdown language switcher for English / Kannada / Hindi.
 * Reads and writes from the LanguageContext provider.
 */
export function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();

  return (
    <select
      id="language-switcher"
      aria-label="Select language"
      value={language}
      onChange={(e) => setLanguage(e.target.value as typeof language)}
      className="rounded-lg border border-line/60 bg-panel/80 px-3 py-1.5 text-sm text-copy transition hover:border-accent/50 focus:border-accent focus:outline-none"
    >
      {languageOptions.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { type AppLanguage, t } from "@/lib/i18n";

const STORAGE_KEY = "sanchar_sarthi_language";

type LanguageContextValue = {
  language: AppLanguage;
  setLanguage: (lang: AppLanguage) => void;
};

const LanguageContext = createContext<LanguageContextValue>({
  language: "en",
  setLanguage: () => {},
});

export function useLanguage(): LanguageContextValue {
  return useContext(LanguageContext);
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<AppLanguage>("en");

  useEffect(() => {
    const stored = globalThis.localStorage?.getItem(STORAGE_KEY);
    if (stored === "kn" || stored === "en") {
      setLanguageState(stored);
    }
  }, []);

  const setLanguage = (lang: AppLanguage) => {
    setLanguageState(lang);
    globalThis.localStorage?.setItem(STORAGE_KEY, lang);
    if (lang === "kn") {
      document.cookie = `googtrans=/en/kn; path=/;`;
    } else {
      document.cookie = `googtrans=/en/en; path=/;`;
      document.cookie = `googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
    }
    window.location.reload();
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useI18n() {
  const { language } = useLanguage();
  return {
    t: (key: string) => t(language, key),
    language
  };
}

"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { dictionary, Locale } from "@/lib/dictionary";

interface LocaleContextValue {
  locale: Locale;
  t: typeof dictionary["ar"];
  toggleLocale: () => void;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("ar");

  useEffect(() => {
    const stored = localStorage.getItem("wolfhost_locale") as Locale | null;
    if (stored) setLocale(stored);
  }, []);

  useEffect(() => {
    document.documentElement.dir = dictionary[locale].dir;
    document.documentElement.lang = locale;
    localStorage.setItem("wolfhost_locale", locale);
  }, [locale]);

  const toggleLocale = () => setLocale((prev) => (prev === "ar" ? "en" : "ar"));

  return (
    <LocaleContext.Provider value={{ locale, t: dictionary[locale], toggleLocale }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const context = useContext(LocaleContext);
  if (!context) throw new Error("useLocale must be used within LocaleProvider");
  return context;
}

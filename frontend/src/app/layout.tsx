import type { Metadata } from "next";
import { LocaleProvider } from "@/hooks/useLocale";
import "./globals.css";

export const metadata: Metadata = {
  title: "Wolf Host — منصة استضافة بوتات بايثون",
  description: "Wolf Host — Professional Python bot hosting platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body className="font-body min-h-screen antialiased">
        <LocaleProvider>{children}</LocaleProvider>
      </body>
    </html>
  );
}

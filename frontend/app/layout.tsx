import type { ReactNode } from "react";
import type { Metadata } from "next";

import { AppProviders } from "@/components/app-providers";
import { LanguageProvider } from "@/components/LanguageContext";

import "./globals.css";

export const metadata: Metadata = {
  title: "Sanchar Sarthi",
  description: "Predictive traffic command twin for Bengaluru event-driven congestion."
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>
        <LanguageProvider>
          <AppProviders>{children}</AppProviders>
        </LanguageProvider>
      </body>
    </html>
  );
}


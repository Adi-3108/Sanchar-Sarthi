import type { ReactNode } from "react";
import type { Metadata } from "next";

import { AppProviders } from "@/components/app-providers";

import "./globals.css";

export const metadata: Metadata = {
  title: "EventFlow AI",
  description: "Predictive traffic command twin for Bengaluru event-driven congestion."
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}

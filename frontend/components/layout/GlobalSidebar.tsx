"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUIStore } from "@/lib/stores/useUIStore";
import { useSessionStore, type AccessLevel } from "@/lib/stores/useSessionStore";
import { useEffect, useState } from "react";
import { useLanguage } from "@/components/LanguageContext";
import { t } from "@/lib/i18n";

const NAV_STRUCTURE = [
  {
    title: "portals", // Will map if added to i18n
    links: [
      { name: "commandCenter", href: "/command-center" },
      { name: "controlRoom", href: "/control-room" },
      { name: "officerPortal", href: "/officer" },
      { name: "adminPortal", href: "/admin" },
      { name: "userMode", href: "/user" }
    ]
  },
  {
    title: "dashboards",
    links: [
      { name: "mapIntelligence", href: "/map-intelligence" },
      { name: "explorer", href: "/explorer" },
      { name: "reports", href: "/reports" }
    ]
  },
  {
    title: "intelligence",
    links: [
      { name: "modelInsights", href: "/model-insights" },
      { name: "simulation", href: "/simulation" },
      { name: "postEventLearning", href: "/post-event-learning" }
    ]
  },
  {
    title: "system",
    links: [
      { name: "settings", href: "/settings" }
    ]
  }
];

export function GlobalSidebar() {
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const pathname = usePathname();
  const session = useSessionStore();
  const { language } = useLanguage();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const currentRole = mounted ? session.accessLevel : "public_citizen";

  const visibleGroups = NAV_STRUCTURE.map((group) => {
    return {
      ...group,
      links: group.links
    };
  }).filter((group) => group.links.length > 0);

  // Auto-close on path change
  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname, setSidebarOpen]);

  if (!sidebarOpen) return null;

  return (
    <>
      <div 
        className="fixed inset-0 z-[60] bg-slate-900/40 backdrop-blur-sm transition-opacity" 
        onClick={() => setSidebarOpen(false)} 
      />
      <aside className="fixed inset-y-0 left-0 z-[70] w-72 flex-col overflow-y-auto border-r border-line bg-panel p-6 shadow-2xl transition-transform">
        <div className="flex items-center justify-between mb-8">
          <Link href="/" className="flex items-center gap-3" onClick={() => setSidebarOpen(false)}>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-white font-bold">
              SS
            </div>
            <span className="text-lg font-bold tracking-tight text-copy">{t(language, "appName")}</span>
          </Link>
          <button 
            onClick={() => setSidebarOpen(false)} 
            className="p-2 -mr-2 rounded-xl text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <nav className="flex flex-col gap-6">
          {visibleGroups.map((group) => (
            <div key={group.title}>
              <h3 className="mb-2 px-2 text-xs font-semibold uppercase tracking-widest text-accentSoft">
                {t(language, group.title)}
              </h3>
              <div className="flex flex-col gap-1">
                {group.links.map((link) => {
                  const isActive = pathname === link.href || pathname.startsWith(`${link.href}/`);
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={() => setSidebarOpen(false)}
                      className={`block rounded-xl px-4 py-2.5 text-sm font-medium transition ${
                        isActive
                          ? "bg-accent/10 text-accent"
                          : "text-copy hover:bg-bg"
                      }`}
                    >
                      {t(language, link.name)}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>
    </>
  );
}

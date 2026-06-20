"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { logoutFirebase } from "@/lib/auth";
import { type AccessLevel, useSessionStore } from "@/lib/stores/useSessionStore";
import { useUIStore } from "@/lib/stores/useUIStore";
import { useState, useEffect } from "react";
import { useLanguage } from "@/components/LanguageContext";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { t } from "@/lib/i18n";

type NavLink = {
  name: string;
  href: string;
  roles?: AccessLevel[]; // If undefined, visible to all
};

type NavGroup = {
  title: string;
  links: NavLink[];
};

const NAV_STRUCTURE: NavGroup[] = [
  {
    title: "portals",
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

export function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const session = useSessionStore();
  const { toggleSidebar } = useUIStore();
  const { language } = useLanguage();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // During SSR and hydration, always use "public_citizen" to prevent hydration mismatch.
  // Once mounted, use the actual session access level.
  const currentRole = mounted ? session.accessLevel : "public_citizen";

  async function handleLogout() {
    await logoutFirebase();
    session.clearSession();
    router.push("/");
  }

  // Filter groups based on role
  const visibleGroups = NAV_STRUCTURE.map((group) => {
    return {
      ...group,
      links: group.links
    };
  }).filter((group) => group.links.length > 0);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-line bg-panel/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center px-6 md:px-10">
        <button 
          onClick={toggleSidebar} 
          className="p-2 -ml-2 mr-3 rounded-xl text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition-colors" 
          aria-label="Toggle sidebar"
          type="button"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <Link href="/" className="mr-8 flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-white font-bold">
            SS
          </div>
          <span className="text-lg font-bold tracking-tight text-copy">{t(language, "appName")}</span>
        </Link>

        <nav className="flex h-full items-center gap-6">
          {visibleGroups.map((group) => (
            <div key={group.title} className="group relative flex h-full items-center">
              <button className="flex h-full items-center gap-1.5 text-sm font-semibold text-muted transition hover:text-copy capitalize">
                {t(language, group.title)}
                <svg
                  className="h-4 w-4 opacity-50 transition-transform group-hover:rotate-180"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {/* Dropdown Menu */}
              <div className="pointer-events-none absolute left-0 top-full w-56 -translate-y-2 opacity-0 transition-all duration-200 group-hover:pointer-events-auto group-hover:translate-y-0 group-hover:opacity-100">
                <div className="mt-1 overflow-hidden rounded-2xl border border-line bg-panel p-2 shadow-panel">
                  {group.links.map((link) => {
                    const isActive = pathname === link.href || pathname.startsWith(`${link.href}/`);
                    return (
                      <Link
                        key={link.href}
                        href={link.href}
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
            </div>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-4">
          <LanguageSwitcher />
          <div className="flex flex-col text-right">
            <span className="text-xs font-semibold uppercase tracking-wider text-accentSoft">
              {t(language, "currentRole") || "Current Role"}
            </span>
            <span className="text-sm font-medium text-copy capitalize">
              {t(language, currentRole)}
            </span>
          </div>
          {currentRole !== "public_citizen" && (
            <button
              onClick={handleLogout}
              className="ml-2 rounded-xl border border-line bg-panel px-4 py-2 text-sm font-semibold text-copy transition hover:border-accent hover:text-accent"
            >
              {t(language, "logout")}
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

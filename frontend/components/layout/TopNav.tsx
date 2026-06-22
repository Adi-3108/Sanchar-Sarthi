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
import { useQuery } from "@tanstack/react-query";
import { getUserStats } from "@/lib/api";

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
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const statsQuery = useQuery({
    queryKey: ["user-stats"],
    queryFn: getUserStats,
    enabled: mounted && currentRole !== "public_citizen",
    staleTime: 60_000,
    retry: false,
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (session.showLoginSuccess) {
      const timer = setTimeout(() => {
        session.setLoginSuccess(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [session.showLoginSuccess, session]);

  // During SSR and hydration, always use "public_citizen" to prevent hydration mismatch.
  // Once mounted, use the actual session access level.
  const currentRole = mounted ? session.accessLevel : "public_citizen";

  async function handleLogout() {
    await logoutFirebase();
    session.clearSession();
    setIsProfileOpen(false);
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
    <>
      {session.showLoginSuccess && (
        <div className="fixed bottom-6 right-6 z-[100] flex items-center gap-3 rounded-2xl bg-emerald-500 px-6 py-4 text-white shadow-xl animate-in fade-in slide-in-from-bottom-5">
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span className="font-semibold">Login Successful!</span>
          <button onClick={() => session.setLoginSuccess(false)} className="ml-4 opacity-70 hover:opacity-100">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
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
            {currentRole !== "public_citizen" ? (
              <div className="relative ml-2">
                <button
                  onClick={() => setIsProfileOpen(!isProfileOpen)}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-accent text-white font-bold transition hover:bg-accent/90 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"
                >
                  {session.email ? session.email.charAt(0).toUpperCase() : "U"}
                </button>
                
                {isProfileOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setIsProfileOpen(false)}></div>
                    <div className="absolute right-0 top-full mt-2 w-64 rounded-2xl border border-line bg-panel p-4 shadow-panel animate-in fade-in slide-in-from-top-2 z-50">
                    <div className="mb-4 border-b border-line pb-4">
                      <p className="text-sm font-semibold text-copy truncate">{session.email ?? "User"}</p>
                      <p className="mt-1 text-xs text-muted capitalize">{t(language, currentRole)}</p>
                    </div>
                    <div className="mb-4 space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted">Incidents reported</span>
                        <span className="font-semibold text-copy">
                          {statsQuery.isLoading ? "…" : (statsQuery.data?.incidents_reported ?? 0)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted">Incidents voted</span>
                        <span className="font-semibold text-copy">
                          {statsQuery.isLoading ? "…" : (statsQuery.data?.incidents_voted ?? 0)}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full rounded-xl border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm font-semibold text-rose-600 transition hover:bg-rose-100 hover:text-rose-700"
                    >
                      {t(language, "logout")}
                    </button>
                  </div>
                  </>
                )}
              </div>
            ) : (
              <Link
                href="/login"
                className="ml-2 rounded-xl border border-line bg-panel px-4 py-2 text-sm font-semibold text-copy transition hover:border-accent hover:text-accent"
              >
                {t(language, "login") || "Login"}
              </Link>
            )}
          </div>
        </div>
      </header>
    </>
  );
}

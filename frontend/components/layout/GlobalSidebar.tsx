"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUIStore } from "@/lib/stores/useUIStore";
import { useSessionStore, type AccessLevel } from "@/lib/stores/useSessionStore";
import { useEffect, useState } from "react";

const NAV_STRUCTURE = [
  {
    title: "Portals",
    links: [
      { name: "Command Center", href: "/command-center" },
      { name: "Control Room", href: "/control-room" },
      { name: "Officer Portal", href: "/officer" },
      { name: "Admin Portal", href: "/admin" },
      { name: "User Mode", href: "/user" }
    ]
  },
  {
    title: "Dashboards",
    links: [
      { name: "Map Intelligence", href: "/map-intelligence" },
      { name: "Explorer", href: "/explorer" },
      { name: "Reports", href: "/reports" }
    ]
  },
  {
    title: "Intelligence",
    links: [
      { name: "Model Insights", href: "/model-insights" },
      { name: "Simulation", href: "/simulation" },
      { name: "Post-Event Learning", href: "/post-event-learning" }
    ]
  },
  {
    title: "System",
    links: [
      { name: "Settings (Demo Data)", href: "/settings" }
    ]
  }
];

export function GlobalSidebar() {
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const pathname = usePathname();
  const session = useSessionStore();
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
            <span className="text-lg font-bold tracking-tight text-copy">Sanchar Sarthi</span>
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
                {group.title}
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
                      {link.name}
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

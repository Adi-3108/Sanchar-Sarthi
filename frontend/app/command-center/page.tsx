"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { getCommandCenterSummary } from "@/lib/api";
import { useLanguage } from "@/components/LanguageContext";
import { t } from "@/lib/i18n";
import CorridorRiskTimeline from "./components/CorridorRiskTimeline";
import { Skeleton } from "@/components/ui/Skeleton";

export default function CommandCenterPage() {
  const { language } = useLanguage();
  const [selectedCorridor, setSelectedCorridor] = useState("ORR");
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["command-center-summary"],
    queryFn: getCommandCenterSummary,
    retry: 1,
    refetchOnWindowFocus: false
  });

  const commandCards = [
    {
      title: t(language, "predict"),
      description: t(language, "predictDesc")
    },
    {
      title: t(language, "plan"),
      description: t(language, "planDesc")
    },
    {
      title: t(language, "adapt"),
      description: t(language, "adaptDesc")
    }
  ];

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">

        <section className="overflow-hidden rounded-[28px] border border-line/80 bg-panel/90 p-8 shadow-panel">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">
                {t(language, "appName")}
              </p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
                {t(language, "appTagline")}
              </h1>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link
                  href="/model-insights"
                  className="rounded-full border border-accent/40 bg-accent/10 px-4 py-2 text-sm text-copy transition hover:border-accent hover:bg-accent/20"
                >
                  {t(language, "openModelInsights")}
                </Link>
                <Link
                  href="/reports"
                  className="rounded-full border border-cyan-300/40 bg-cyan-300/10 px-4 py-2 text-sm text-copy transition hover:border-cyan-200 hover:bg-cyan-300/20"
                >
                  {t(language, "submitReport")}
                </Link>
                <Link
                  href="/map-intelligence"
                  className="rounded-full border border-amber-300/40 bg-amber-300/10 px-4 py-2 text-sm text-copy transition hover:border-amber-200 hover:bg-amber-300/20"
                >
                  {t(language, "openMapIntelligence")}
                </Link>
                <Link
                  href="/post-event-learning"
                  className="rounded-full border border-emerald-300/40 bg-emerald-300/10 px-4 py-2 text-sm text-copy transition hover:border-emerald-200 hover:bg-emerald-300/20"
                >
                  {t(language, "openPostEventLearning")}
                </Link>
                <Link
                  href="/settings"
                  className="rounded-full border border-sky-300/40 bg-sky-300/10 px-4 py-2 text-sm text-copy transition hover:border-sky-200 hover:bg-sky-300/20"
                >
                  {t(language, "openDemoReadiness")}
                </Link>
              </div>
            </div>
            <div className="rounded-3xl border border-accent/30 bg-accent/10 px-5 py-4">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">
                {t(language, "systemState")}
              </p>
              <div className="mt-2 text-2xl font-semibold text-copy">
                {isLoading ? (
                  <Skeleton.Line width="w-32" height="h-8" className="bg-accent/20" />
                ) : isError ? (
                  t(language, "attentionNeeded")
                ) : (
                  t(language, "operational")
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-5 md:grid-cols-3">
          {commandCards.map((card) => (
            <article
              key={card.title}
              className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel"
            >
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">{card.title}</p>
              <h2 className="mt-3 text-2xl font-semibold text-copy">{card.title}</h2>
              <p className="mt-3 text-sm leading-7 text-muted">{card.description}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <article className="rounded-[24px] border border-line/70 bg-panel/85 p-6 shadow-panel">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">
                  {t(language, "commandCenter")}
                </p>
                <h2 className="mt-2 text-2xl font-semibold">{t(language, "systemState")}</h2>
              </div>
            </div>

            <div className="mt-6 rounded-3xl border border-line/70 bg-bg/60 p-5 font-mono text-sm leading-7 text-copy">
              {isLoading ? <Skeleton.DataGrid count={8} cols={2} /> : null}
              {isError && (
                <div className="space-y-2 text-danger">
                  <p>{t(language, "backendFailed")}</p>
                  <p className="text-xs text-muted">{error instanceof Error ? error.message : "Unknown error"}</p>
                </div>
              )}
              {data && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-muted">{t(language, "activeEvents")}:</span>
                    <span className="ml-2 font-semibold text-accent">{data.activeEvents}</span>
                  </div>
                  <div>
                    <span className="text-muted">{t(language, "criticalEvents")}:</span>
                    <span className="ml-2 font-semibold text-danger">{data.criticalEvents}</span>
                  </div>
                  <div>
                    <span className="text-muted">{t(language, "hotspots")}:</span>
                    <span className="ml-2 font-semibold text-amber-400">{data.hotspotCount}</span>
                  </div>
                  <div>
                    <span className="text-muted">{t(language, "pendingReports")}:</span>
                    <span className="ml-2 font-semibold text-sky-400">{data.pendingReports}</span>
                  </div>
                  <div>
                    <span className="text-muted">{t(language, "resolvedToday")}:</span>
                    <span className="ml-2 font-semibold text-emerald-400">{data.resolvedToday}</span>
                  </div>
                  <div>
                    <span className="text-muted">{t(language, "recommendations")}:</span>
                    <span className="ml-2 font-semibold text-accent">{data.latestRecommendationCount}</span>
                  </div>
                  <div>
                    <span className="text-muted">{t(language, "totalEvents")}:</span>
                    <span className="ml-2 font-semibold">{data.totalEvents}</span>
                  </div>
                  <div>
                    <span className="text-muted">{t(language, "totalIncidents")}:</span>
                    <span className="ml-2 font-semibold">{data.totalIncidents}</span>
                  </div>
                </div>
              )}
            </div>
          </article>

          <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel">
            <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">{t(language, "capabilities")}</p>
            <h2 className="mt-2 text-2xl font-semibold">{t(language, "capabilities")}</h2>
            <ul className="mt-5 space-y-3 text-sm leading-7 text-muted">
              <li>{t(language, "cap1")}</li>
              <li>{t(language, "cap2")}</li>
              <li>{t(language, "cap3")}</li>
              <li>{t(language, "cap4")}</li>
              <li>{t(language, "cap5")}</li>
              <li>{t(language, "cap6")}</li>
              <li>{t(language, "cap7")}</li>
              <li>{t(language, "cap8")}</li>
            </ul>
          </article>
        </section>

        <section className="grid gap-5">
          <div className="flex items-center gap-3 bg-panelAlt/90 p-4 border border-line/70 rounded-[24px]">
            <span className="text-sm font-semibold text-copy whitespace-nowrap ml-2">Select Corridor:</span>
            <select
              value={selectedCorridor}
              onChange={(e) => setSelectedCorridor(e.target.value)}
              className="bg-bg/80 border border-line rounded-2xl px-4 py-2 text-sm text-copy outline-none focus:border-accent w-full md:w-auto"
            >
              <option value="ORR">Outer Ring Road (ORR)</option>
              <option value="Tumkur Road">Tumkur Road</option>
              <option value="Hosur Road">Hosur Road</option>
              <option value="Old Madras Road">Old Madras Road</option>
              <option value="Bellary Road">Bellary Road</option>
              <option value="Bannerghatta Road">Bannerghatta Road</option>
            </select>
          </div>
          <div className="w-full">
            <CorridorRiskTimeline corridor={selectedCorridor} />
          </div>
        </section>
      </div>
    </main>
  );
}


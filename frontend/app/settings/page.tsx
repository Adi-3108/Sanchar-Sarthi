"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import {
  ApiError,
  getDemoStatus,
  getHealth,
  getMapConfig,
  seedDemoScenarios,
  type DemoCheckResponse,
  type DemoScenarioCardResponse,
  type DemoSeedResponse,
  type DemoStatusResponse,
} from "@/lib/api";
import { handleError, errorText as getErrorText } from "@/lib/errorHandler";
import { useFirebaseAuthState } from "@/lib/auth";
import { useCommandStore } from "@/lib/stores/useCommandStore";
import { Skeleton } from "@/components/ui/Skeleton";
import { toast } from "sonner";



function statusLabel(status: string | undefined): string {
  return status === "ready" ? "Judge demo ready" : "Needs seeding or verification";
}

function sampleEventId(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function sampleEventIds(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => String(item)).filter(Boolean);
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { user, ready: authReady } = useFirebaseAuthState();
  const { setSelectedEventId } = useCommandStore();

  const healthQuery = useQuery({
    queryKey: ["settings-health"],
    queryFn: getHealth,
    retry: 1,
    refetchOnWindowFocus: false,
  });
  const mapQuery = useQuery({
    queryKey: ["settings-map-config"],
    queryFn: getMapConfig,
    retry: 1,
    refetchOnWindowFocus: false,
  });
  const demoStatusQuery = useQuery({
    queryKey: ["demo-status"],
    queryFn: getDemoStatus,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  const seedMutation = useMutation<DemoSeedResponse, unknown>({
    mutationFn: () => seedDemoScenarios(),
    onSuccess: async (data) => {
      toast.success(data.message || "Demo seeded successfully.");
      await queryClient.invalidateQueries({ queryKey: ["demo-status"] });
    },
    onError: (error) => {
      handleError(error, "Failed to refresh demo seed.");
    }
  });

  const canRunProtectedActions = authReady && Boolean(user);
  const summary = demoStatusQuery.data?.summary;
  const predictPlanId = sampleEventId(demoStatusQuery.data?.sample_event_ids.predict_plan);
  const learningId = sampleEventId(demoStatusQuery.data?.sample_event_ids.learning);
  const coordinationIds = sampleEventIds(demoStatusQuery.data?.sample_event_ids.coordination_pair);

  const headline = useMemo(() => {
    if (seedMutation.data?.message) {
      return seedMutation.data.message;
    }
    return statusLabel(demoStatusQuery.data?.status);
  }, [demoStatusQuery.data?.status, seedMutation.data?.message]);

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="rounded-[28px] border border-line/80 bg-panel/90 p-8 shadow-panel">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">Demo Readiness</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
                Demo readiness and deterministic walkthrough seeding.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted md:text-lg">
                This page checks whether the full product flow is ready for a reliable demo, then
                refreshes the fixed demo events, officer mappings, escalation storyline, and
                learning loop when you run the protected seed action.
              </p>
            </div>

            <div className="flex flex-col gap-3">
              <div className="rounded-3xl border border-accent/30 bg-accent/10 px-5 py-4">
                <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Demo state</p>
                <p className="mt-2 text-2xl font-semibold text-copy">{demoStatusQuery.isLoading ? <Skeleton.Line width="w-52" height="h-7" className="bg-accent/20" /> : headline}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-5 xl:grid-cols-[0.38fr_0.62fr]">
          <AuthPanel
            preferredRole="admin"
            title="Protected controls"
            note="Sign in with an Admin account to refresh the deterministic demo data through the backend."
          />

          <div className="grid gap-5">
            <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
              <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Protected action</p>
                  <h2 className="mt-2 text-2xl font-semibold">Refresh deterministic demo scenarios</h2>
                </div>
                <button
                  type="button"
                  onClick={() => seedMutation.mutate()}
                  disabled={!canRunProtectedActions || seedMutation.isPending}
                  className="rounded-2xl border border-accent/50 bg-accent px-4 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {seedMutation.isPending ? "Refreshing demo seed" : "Refresh demo seed"}
                </button>
              </div>
              <p className="mt-4 text-sm leading-7 text-muted">
                The seed refresh only updates fixed `DEMO_` records, keeps non-demo data untouched,
                and rebuilds the full stack needed for the demo walkthrough.
              </p>
              {!canRunProtectedActions ? (
                <p className="mt-3 text-sm leading-7 text-muted">
                  Sign in before running the protected demo seed action.
                </p>
              ) : null}
            </article>

            <article className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {healthQuery.isLoading || mapQuery.isLoading || demoStatusQuery.isLoading ? (
                <Skeleton.MetricGrid count={4} />
              ) : (
                <>
                  <MetricCard
                    label="Backend"
                    value={healthQuery.data?.database ?? "n/a"}
                    note={`Firebase: ${healthQuery.data?.auth.firebase ?? "n/a"}`}
                  />
                  <MetricCard
                    label="Map Provider"
                    value={mapQuery.data?.activeProvider ?? "n/a"}
                    note={mapQuery.data?.providerNote ?? "MapmyIndia / Mappls only"}
                  />
                  <MetricCard
                    label="Demo Events"
                    value={String(summary?.demo_events ?? 0)}
                    note={`${summary?.demo_hotspot_clusters ?? 0} hotspot clusters`}
                  />
                  <MetricCard
                    label="Learning Loop"
                    value={String(summary?.demo_post_event_reports ?? 0)}
                    note={`${summary?.demo_reports ?? 0} reports / ${summary?.demo_live_updates ?? 0} live updates`}
                  />
                </>
              )}
            </article>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.52fr_0.48fr]">
          <article className="rounded-[24px] border border-line/70 bg-panel/85 p-6 shadow-panel">
            <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Readiness checks</p>
            <h2 className="mt-2 text-2xl font-semibold">Demo completion gates</h2>
            <div className="mt-5 space-y-3">
              {demoStatusQuery.isLoading ? (
                <div className="space-y-3 animate-pulse">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="rounded-2xl border border-line/70 bg-bg/60 p-4">
                      <div className="flex items-center justify-between gap-4">
                        <div className="space-y-2 flex-1">
                          <div className="h-4 w-40 rounded bg-line/60" />
                          <div className="h-3 w-full rounded bg-line/40" />
                        </div>
                        <div className="h-6 w-16 rounded-full bg-line/40" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : demoStatusQuery.data?.checks?.length ? (
                demoStatusQuery.data.checks.map((check) => <ReadinessRow key={check.key} check={check} />)
              ) : (
                <p className="text-sm leading-7 text-muted">
                  {demoStatusQuery.isError
                    ? getErrorText(demoStatusQuery.error)
                    : "No demo readiness checks are available yet."}
                </p>
              )}
            </div>
          </article>

          <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel">
            <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Quick launch</p>
            <h2 className="mt-2 text-2xl font-semibold">Use the seeded walkthrough anchors</h2>
            <div className="mt-5 grid gap-3">
              {demoStatusQuery.isLoading ? (
                <Skeleton.TableRows count={4} />
              ) : (
                <>
                  <QuickLink
                    href={predictPlanId ? `/events/${predictPlanId}` : "/simulation"}
                    label="Predict and plan anchor"
                    note={predictPlanId ?? "Simulation route"}
                    onClick={() => setSelectedEventId(predictPlanId)}
                  />
                  <QuickLink
                    href="/map-intelligence"
                    label="Multi-event coordination"
                    note={coordinationIds.length ? coordinationIds.join(" + ") : "Tumkur overlap pair"}
                    onClick={() => setSelectedEventId(coordinationIds[0])}
                  />
                  <QuickLink
                    href={learningId ? `/events/${learningId}` : "/post-event-learning"}
                    label="Learning event dossier"
                    note={learningId ?? "Post-event learning route"}
                    onClick={() => setSelectedEventId(learningId)}
                  />
                  <QuickLink
                    href="/post-event-learning"
                    label="After-action report"
                    note="Generate the learning panel from the seeded event"
                    onClick={() => setSelectedEventId(learningId)}
                  />
                </>
              )}
            </div>
          </article>
        </section>

        <section className="grid gap-5 lg:grid-cols-2">
          {demoStatusQuery.isLoading ? (
            <Skeleton.ScenarioGrid count={2} />
          ) : (
            (demoStatusQuery.data?.scenario_cards ?? []).map((scenario) => (
              <ScenarioCard
                key={scenario.scenario_name}
                scenario={scenario}
                onSelectEvent={(eventId) => setSelectedEventId(eventId)}
              />
            ))
          )}
        </section>
      </div>
    </main>
  );
}

function MetricCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
      <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">{label}</p>
      <p className="mt-3 text-2xl font-semibold text-copy">{value}</p>
      <p className="mt-2 text-sm leading-7 text-muted">{note}</p>
    </div>
  );
}

function ReadinessRow({ check }: { check: DemoCheckResponse }) {
  return (
    <div className="rounded-2xl border border-line/70 bg-bg/60 p-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-copy">{check.label}</p>
          <p className="mt-1 text-sm leading-7 text-muted">{check.detail}</p>
        </div>
        <span
          className={
            check.ready
              ? "rounded-full border border-emerald-500 bg-emerald-100 px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] text-emerald-800"
              : "rounded-full border border-amber-500 bg-amber-100 px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] text-amber-800"
          }
        >
          {check.ready ? "Ready" : "Check"}
        </span>
      </div>
    </div>
  );
}

function ScenarioCard({
  scenario,
  onSelectEvent,
}: {
  scenario: DemoScenarioCardResponse;
  onSelectEvent: (eventId?: string) => void;
}) {
  return (
    <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="max-w-2xl">
          <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">{scenario.scenario_type}</p>
          <h2 className="mt-2 text-2xl font-semibold">{scenario.scenario_name}</h2>
          <p className="mt-3 text-sm leading-7 text-muted">{scenario.description}</p>
        </div>
        <Link
          href={scenario.route}
          onClick={() => onSelectEvent(scenario.primary_event_id ?? undefined)}
          className="rounded-full border border-accent/40 bg-accent/10 px-4 py-2 text-sm text-copy transition hover:border-accent hover:bg-accent/20"
        >
          Open route
        </Link>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        <div className="rounded-2xl border border-line/70 bg-bg/60 p-4">
          <p className="text-[11px] uppercase tracking-[0.22em] text-accentSoft">Walkthrough</p>
          <div className="mt-3 space-y-2 text-sm leading-7 text-muted">
            {scenario.walkthrough_steps.map((step) => (
              <p key={step}>{step}</p>
            ))}
          </div>
        </div>
        <div className="rounded-2xl border border-line/70 bg-bg/60 p-4">
          <p className="text-[11px] uppercase tracking-[0.22em] text-accentSoft">Expected highlights</p>
          <div className="mt-3 space-y-2 text-sm leading-7 text-muted">
            {scenario.expected_highlights.map((highlight) => (
              <p key={highlight}>{highlight}</p>
            ))}
          </div>
        </div>
      </div>

      {scenario.event_ids.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {scenario.event_ids.map((eventId) => (
            <Link
              key={eventId}
              href={`/events/${eventId}`}
              onClick={() => onSelectEvent(eventId)}
              className="rounded-full border border-line/80 px-3 py-1 text-xs uppercase tracking-[0.18em] text-muted transition hover:border-accent/60 hover:text-copy"
            >
              {eventId}
            </Link>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function QuickLink({
  href,
  label,
  note,
  onClick,
}: {
  href: string;
  label: string;
  note: string;
  onClick: () => void;
}) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className="rounded-2xl border border-line/70 bg-bg/60 p-4 transition hover:border-accent/60 hover:bg-bg/80"
    >
      <p className="text-sm font-semibold text-copy">{label}</p>
      <p className="mt-2 text-sm leading-7 text-muted">{note}</p>
    </Link>
  );
}


"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import {
  generateEventPlan,
  getEventDetail,
  submitLiveUpdate,
  type EventPlanRequest,
  type LiveUpdateRequest,
  type RecommendationPlanResponse
} from "@/lib/api";
import { useFirebaseAuthState } from "@/lib/auth";
import { useCommandStore } from "@/lib/stores/useCommandStore";

type EventDetailPageProps = {
  params: {
    id: string;
  };
};

function formatDate(value?: string | null): string {
  if (!value) {
    return "n/a";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "n/a";
  }
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(parsed);
}

export default function EventDetailPage({ params }: EventDetailPageProps) {
  const queryClient = useQueryClient();
  const { user, ready: authReady } = useFirebaseAuthState();
  const { setSelectedEventId } = useCommandStore();
  const eventId = decodeURIComponent(params.id);
  const [availableOfficers, setAvailableOfficers] = useState("10");
  const [fieldUpdate, setFieldUpdate] = useState("Field team reports crowd spillover and slow movement.");

  useEffect(() => {
    setSelectedEventId(eventId);
  }, [eventId, setSelectedEventId]);

  const detailQuery = useQuery({
    queryKey: ["event-detail", eventId],
    queryFn: () => getEventDetail(eventId),
    enabled: authReady && Boolean(user),
    retry: 1,
    refetchOnWindowFocus: false
  });
  const planMutation = useMutation<RecommendationPlanResponse, unknown, EventPlanRequest>({
    mutationFn: (payload) => generateEventPlan(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["event-detail", eventId] });
    }
  });
  const liveUpdateMutation = useMutation({
    mutationFn: (payload: LiveUpdateRequest) => submitLiveUpdate(eventId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["event-detail", eventId] });
    }
  });

  function handlePlanSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    planMutation.mutate({
      event_id: eventId,
      available_officers: Number(availableOfficers),
      include_logistics_impact: true,
      include_emergency_corridor: true
    });
  }

  function handleLiveUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    liveUpdateMutation.mutate({
      current_congestion_level: "Warning",
      field_update: fieldUpdate,
      crowd_increase: true,
      road_closure_active: false,
      officer_shortage: false,
      rain_waterlogging: false,
      new_nearby_incident: false
    });
  }

  const detail = detailQuery.data;
  const recommendation = planMutation.data ?? detail?.recommendation;

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="rounded-[28px] border border-line/80 bg-panel/90 p-8 shadow-panel">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">Event dossier</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">{eventId}</h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
                Protected dossier view for Event DNA, predictions, recommendations, citizen reports, and live updates.
              </p>
            </div>
            <nav className="flex flex-wrap gap-3">
              <Link href="/explorer" className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy">
                Explorer
              </Link>
              <Link href="/officer" className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy">
                Officer portal
              </Link>
            </nav>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.34fr_0.66fr]">
          <aside className="space-y-5">
            <AuthPanel
              preferredRole="control_room"
              title="Protected dossier sign-in"
              note="This dossier loads only for internal Level 1 users or officers assigned to the event, corridor, station, or zone."
            />

            {detail ? (
              <>
                <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
                  <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Event</p>
                  <div className="mt-4 grid gap-3">
                    <Metric label="Cause" value={detail.event.event_cause_clean ?? "n/a"} />
                    <Metric label="Priority" value={detail.event.priority ?? "n/a"} />
                    <Metric label="Corridor" value={detail.event.corridor ?? "n/a"} />
                    <Metric label="Start" value={formatDate(detail.event.start_datetime)} />
                  </div>
                </article>

                <article className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
                  <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Prediction</p>
                  <div className="mt-4 grid gap-3">
                    <Metric label="Impact score" value={detail.prediction?.estimated_impact_score?.toFixed(1) ?? "n/a"} />
                    <Metric label="Impact category" value={detail.prediction?.impact_category ?? "n/a"} />
                    <Metric label="Clearance" value={detail.prediction?.estimated_clearance_minutes ? `${Math.round(detail.prediction.estimated_clearance_minutes)} min` : "n/a"} />
                    <Metric label="Road closure" value={detail.prediction?.road_closure_probability ? `${Math.round(detail.prediction.road_closure_probability * 100)}%` : "n/a"} />
                  </div>
                </article>

                <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
                  <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Activity</p>
                  <div className="mt-4 grid gap-3">
                    <Metric label="Similar events" value={String(detail.similar_events.length)} />
                    <Metric label="Citizen reports" value={String(detail.citizen_reports.length)} />
                    <Metric label="Live updates" value={String(detail.live_updates.length)} />
                  </div>
                </article>
              </>
            ) : null}
          </aside>

          <div className="space-y-5">
            {detailQuery.isLoading ? <p className="text-sm text-muted">Loading event dossier...</p> : null}
            {!authReady ? <p className="text-sm text-muted">Restoring protected dossier session...</p> : null}
            {authReady && !user ? <p className="text-sm text-muted">Sign in to load this protected event dossier.</p> : null}
            {detailQuery.isError ? (
              <section className="rounded-[24px] border border-danger/30 bg-danger/10 p-5 text-sm leading-7 text-danger shadow-panel">
                Event detail requires an authenticated Level 1 or assigned Level 2 Firebase session. The event ID route is wired,
                but backend authorization remains mandatory.
              </section>
            ) : null}

            {detail ? (
              <>
                <article className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
                  <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Event DNA</p>
                  <h2 className="mt-2 text-2xl font-semibold">{detail.event_dna?.time_context ?? "DNA not generated yet"}</h2>
                  <p className="mt-4 text-sm leading-7 text-muted">{detail.event_dna?.dna_summary ?? "Run the backend DNA rebuild pipeline to populate this event."}</p>
                </article>

                <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
                  <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Recommendation</p>
                      <h2 className="mt-2 text-2xl font-semibold">Generate event plan</h2>
                    </div>
                    <form onSubmit={handlePlanSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-end">
                      <label className="text-sm text-muted">
                        <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Officers</span>
                        <input
                          value={availableOfficers}
                          onChange={(event) => setAvailableOfficers(event.target.value)}
                          className="w-32 rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                        />
                      </label>
                      <button
                        type="submit"
                        disabled={!user || planMutation.isPending}
                        className="rounded-2xl border border-accent/50 bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {planMutation.isPending ? "Generating" : "Generate"}
                      </button>
                    </form>
                  </div>
                  {recommendation ? (
                    <div className="mt-5 space-y-4">
                      <p className="text-sm leading-7 text-muted">{recommendation.recommended_action_summary}</p>
                      <div className="grid gap-3 sm:grid-cols-3">
                        <Metric label="Officers" value={String(recommendation.manpower.recommended_total_officers)} />
                        <Metric label="Barricades" value={String(recommendation.barricades.estimated_units)} />
                        <Metric label="Diversion" value={recommendation.diversions.strategy} />
                      </div>
                    </div>
                  ) : (
                    <p className="mt-5 text-sm leading-7 text-muted">No recommendation is attached yet.</p>
                  )}
                  {planMutation.isError ? <p className="mt-4 text-sm text-danger">Plan generation needs internal access for this event.</p> : null}
                </article>

                <form onSubmit={handleLiveUpdate} className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
                  <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Monitor and adapt</p>
                  <label className="mt-4 block text-sm text-muted">
                    <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Field update</span>
                    <textarea
                      value={fieldUpdate}
                      onChange={(event) => setFieldUpdate(event.target.value)}
                      rows={4}
                      className="w-full resize-none rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                    />
                  </label>
                  <button
                    type="submit"
                    disabled={!user || liveUpdateMutation.isPending}
                    className="mt-4 rounded-2xl border border-accent/50 bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {liveUpdateMutation.isPending ? "Submitting" : "Submit live update"}
                  </button>
                  {liveUpdateMutation.data ? (
                    <p className="mt-4 text-sm leading-7 text-ok">
                      Accepted with current score {liveUpdateMutation.data.current_impact_score.toFixed(1)}.
                    </p>
                  ) : null}
                  {liveUpdateMutation.isError ? <p className="mt-4 text-sm text-danger">Live update was not accepted for this session.</p> : null}
                </form>
              </>
            ) : null}
          </div>
        </section>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line/70 bg-bg/60 p-4">
      <p className="text-[11px] uppercase tracking-[0.22em] text-accentSoft">{label}</p>
      <p className="mt-2 text-sm font-semibold text-copy">{value}</p>
    </div>
  );
}

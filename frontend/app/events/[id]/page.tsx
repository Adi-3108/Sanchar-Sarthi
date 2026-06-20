"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import ActionConfidenceLedger from "@/components/recommendations/ActionConfidenceLedger";
import BarricadePlanPanel from "@/components/recommendations/BarricadePlanPanel";
import CounterfactualImpactCard from "@/components/recommendations/CounterfactualImpactCard";
import DiversionPlanPanel from "@/components/recommendations/DiversionPlanPanel";
import EmergencyCorridorPanel from "@/components/recommendations/EmergencyCorridorPanel";
import EventDNACard from "@/components/recommendations/EventDNACard";
import FlipkartLogisticsImpactPanel from "@/components/recommendations/FlipkartLogisticsImpactPanel";
import ImpactScorePanel from "@/components/recommendations/ImpactScorePanel";
import LiveEscalationTimeline from "@/components/recommendations/LiveEscalationTimeline";
import ManpowerPlanPanel from "@/components/recommendations/ManpowerPlanPanel";
import SimilarEventMemoryPanel from "@/components/recommendations/SimilarEventMemoryPanel";
import WeatherRiskPanel from "@/components/recommendations/WeatherRiskPanel";
import {
  generateEventPlan,
  getEventDetail,
  submitLiveUpdate,
  type EventCitizenReportRecordResponse,
  type EventDetailResponse,
  type EventPlanRequest,
  type EventPredictionResponse,
  type LiveUpdateRequest,
  type LiveUpdateResponse,
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

function formatPercent(value?: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

function formatNumber(value?: number | null, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return value.toFixed(digits);
}

function predictionScoreReasonCodes(prediction?: EventPredictionResponse | null): string[] {
  const impactRoot = prediction?.prediction_explanation_json?.impact;
  if (!impactRoot || typeof impactRoot !== "object") {
    return [];
  }

  const impactRecord = impactRoot as Record<string, unknown>;
  const nestedImpact =
    "impact" in impactRecord && impactRecord.impact && typeof impactRecord.impact === "object"
      ? (impactRecord.impact as Record<string, unknown>)
      : impactRecord;
  const reasonCodes = nestedImpact.score_reason_codes;
  return Array.isArray(reasonCodes) ? reasonCodes.filter((value): value is string => typeof value === "string") : [];
}

function counterfactualHonestyNote(prediction?: EventPredictionResponse | null): string | null {
  const impactRoot = prediction?.prediction_explanation_json?.impact;
  if (!impactRoot || typeof impactRoot !== "object") {
    return null;
  }
  const impactRecord = impactRoot as Record<string, unknown>;
  const counterfactual =
    "counterfactual" in impactRecord && impactRecord.counterfactual && typeof impactRecord.counterfactual === "object"
      ? (impactRecord.counterfactual as Record<string, unknown>)
      : null;
  return typeof counterfactual?.honesty_note === "string" ? counterfactual.honesty_note : null;
}

function reportHeadline(report: EventCitizenReportRecordResponse): string {
  return report.translated_description || report.description || "No description provided.";
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
    onSuccess: async (plan) => {
      queryClient.setQueryData<EventDetailResponse | undefined>(["event-detail", eventId], (current) =>
        current
          ? {
              ...current,
              recommendation: plan
            }
          : current
      );
      await queryClient.invalidateQueries({ queryKey: ["event-detail", eventId] });
    }
  });
  const liveUpdateMutation = useMutation<LiveUpdateResponse, unknown, LiveUpdateRequest>({
    mutationFn: (payload) => submitLiveUpdate(eventId, payload),
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
  const recommendation = detail?.recommendation;
  const prediction = detail?.prediction;
  const scoreReasonCodes = useMemo(() => predictionScoreReasonCodes(prediction), [prediction]);
  const counterfactualNote = useMemo(() => counterfactualHonestyNote(prediction), [prediction]);

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex w-full max-w-[1800px] flex-col gap-8">
        <section className="rounded-[28px] border border-line/80 bg-panel/90 p-8 shadow-panel">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">Event dossier</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">{eventId}</h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
                Protected dossier view for Event DNA, predictions, recommendations, citizen reports, and live updates.
              </p>
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.22fr_0.56fr_0.22fr]">
          <aside className="space-y-5">
            <AuthPanel
              preferredRole="control_room"
              title="Protected dossier sign-in"
              note="This dossier loads only for internal Level 1 users or officers assigned to the event, corridor, station, or zone."
            />

            {detail ? (
              <>
                <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
                  <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Event snapshot</p>
                  <div className="mt-4 grid gap-3">
                    <Metric label="Cause" value={detail.event.event_cause_clean ?? "n/a"} />
                    <Metric label="Priority" value={detail.event.priority ?? "n/a"} />
                    <Metric label="Corridor" value={detail.event.corridor ?? "n/a"} />
                    <Metric label="Police station" value={detail.event.police_station ?? "n/a"} />
                    <Metric label="Start" value={formatDate(detail.event.start_datetime)} />
                    <Metric label="Status" value={detail.event.status ?? "n/a"} />
                  </div>
                </article>

                <article className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
                  <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Signals</p>
                  <div className="mt-4 grid gap-3">
                    <Metric label="Impact score" value={formatNumber(prediction?.estimated_impact_score)} />
                    <Metric label="Impact category" value={prediction?.impact_category ?? "n/a"} />
                    <Metric
                      label="Road closure"
                      value={formatPercent(prediction?.road_closure_probability)}
                    />
                    <Metric
                      label="Weather source"
                      value={prediction?.weather_adjustment_json?.source ?? "n/a"}
                    />
                    <Metric label="Similar events" value={String(detail.similar_events.length)} />
                    <Metric label="Live updates" value={String(detail.live_updates.length)} />
                  </div>
                </article>

                <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
                  <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Citizen and field reports</p>
                  <div className="mt-4 grid gap-3">
                    {detail.citizen_reports.length ? (
                      detail.citizen_reports.slice(0, 4).map((report) => (
                        <div key={report.id} className="rounded-2xl border border-line/70 bg-bg/60 p-4">
                          <p className="text-[11px] uppercase tracking-[0.18em] text-accentSoft">
                            {report.report_source.replaceAll("_", " ")}
                          </p>
                          <p className="mt-2 text-sm leading-7 text-copy">{reportHeadline(report)}</p>
                          <p className="mt-2 text-xs text-muted">
                            {report.new_alert_level ?? "Info"} alert, {formatPercent(report.report_confidence)} confidence
                          </p>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-muted">No linked citizen or field reports yet.</p>
                    )}
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
                <EventDNACard eventDna={detail.event_dna} />
                <SimilarEventMemoryPanel similarEvents={detail.similar_events} />

                <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
                  <ImpactScorePanel
                    estimatedImpactScore={prediction?.estimated_impact_score}
                    impactCategory={prediction?.impact_category}
                    impactRadiusKm={prediction?.impact_radius_km}
                    vehicleImpactFactor={prediction?.vehicle_impact_factor}
                    vehicleImpactNote={prediction?.vehicle_impact_note}
                    priorityConfidence={prediction?.priority_confidence}
                    roadClosureProbability={prediction?.road_closure_probability}
                    scoreReasonCodes={scoreReasonCodes}
                  />
                  <div className="grid gap-5">
                    <CounterfactualImpactCard
                      baselineRiskScore={prediction?.baseline_risk_score}
                      eventImpactScore={prediction?.estimated_impact_score}
                      additionalEventDelta={prediction?.additional_event_delta}
                      honestyNote={counterfactualNote}
                    />
                    <WeatherRiskPanel
                      weatherRisk={recommendation?.weather_risk ?? prediction?.weather_adjustment_json}
                    />
                  </div>
                </div>

                <div className="grid gap-5 xl:grid-cols-2">
                  <ManpowerPlanPanel manpower={recommendation?.manpower} />
                  <BarricadePlanPanel barricades={recommendation?.barricades} />
                  <DiversionPlanPanel diversions={recommendation?.diversions} />
                  <EmergencyCorridorPanel emergencyCorridor={recommendation?.emergency_corridor} />
                  <FlipkartLogisticsImpactPanel logisticsImpact={recommendation?.flipkart_logistics_impact} />
                  <ActionConfidenceLedger items={recommendation?.action_confidence_ledger ?? []} />
                </div>


              </>
            ) : null}
          </div>

          <aside className="space-y-5">
            {detail ? (
              <>
                <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
                  <div className="flex flex-col gap-4">
                    <div>
                      <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Recommendation</p>
                      <h2 className="mt-2 text-2xl font-semibold">Generate event plan</h2>
                      <p className="mt-3 text-sm leading-7 text-muted">
                        Regenerate the stored plan for this event and immediately rehydrate the dossier panels below.
                      </p>
                    </div>
                    <form onSubmit={handlePlanSubmit} className="flex flex-col gap-3">
                      <label className="text-sm text-muted">
                        <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Officers</span>
                        <input
                          value={availableOfficers}
                          onChange={(event) => setAvailableOfficers(event.target.value)}
                          className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                        />
                      </label>
                      <button
                        type="submit"
                        disabled={!user || planMutation.isPending}
                        className="w-full rounded-2xl border border-accent/50 bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {planMutation.isPending ? "Generating" : "Generate"}
                      </button>
                    </form>
                  </div>
                  {recommendation ? (
                    <p className="mt-5 text-sm leading-7 text-muted">{recommendation.recommended_action_summary}</p>
                  ) : (
                    <p className="mt-5 text-sm leading-7 text-muted">No recommendation is attached yet.</p>
                  )}
                  {planMutation.isError ? (
                    <p className="mt-4 text-sm text-danger">Plan generation needs internal access for this event.</p>
                  ) : null}
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
                    className="w-full mt-4 rounded-2xl border border-accent/50 bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {liveUpdateMutation.isPending ? "Submitting" : "Submit live update"}
                  </button>
                  {liveUpdateMutation.data ? (
                    <p className="mt-4 text-sm leading-7 text-ok">
                      Accepted with current score {liveUpdateMutation.data.current_impact_score.toFixed(1)}.
                    </p>
                  ) : null}
                  {liveUpdateMutation.isError ? (
                    <p className="mt-4 text-sm text-danger">Live update was not accepted for this session.</p>
                  ) : null}
                </form>

                <LiveEscalationTimeline updates={detail.live_updates} />
              </>
            ) : null}
          </aside>
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



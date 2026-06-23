"use client";

import Link from "next/link";
import { type FormEvent, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import ActionConfidenceLedger from "@/components/recommendations/ActionConfidenceLedger";
import BarricadePlanPanel from "@/components/recommendations/BarricadePlanPanel";
import CounterfactualImpactCard from "@/components/recommendations/CounterfactualImpactCard";
import DiversionPlanPanel from "@/components/recommendations/DiversionPlanPanel";
import EmergencyCorridorPanel from "@/components/recommendations/EmergencyCorridorPanel";
import EventDNACard from "@/components/recommendations/EventDNACard";
import FlipkartLogisticsImpactPanel from "@/components/recommendations/FlipkartLogisticsImpactPanel";
import ImpactScorePanel from "@/components/recommendations/ImpactScorePanel";
import ManpowerPlanPanel from "@/components/recommendations/ManpowerPlanPanel";
import WeatherRiskPanel from "@/components/recommendations/WeatherRiskPanel";
import {
  ApiError,
  simulateEvent,
  type EventPredictionResponse,
  type EventSimulationRequest,
  type EventSimulationResponse
} from "@/lib/api";
import { Skeleton } from "@/components/ui/Skeleton";
import { useFirebaseAuthState } from "@/lib/auth";

type WeatherCondition = NonNullable<EventSimulationRequest["weather_condition"]>;

function tomorrowIsoHour(): string {
  const next = new Date();
  next.setDate(next.getDate() + 1);
  next.setHours(18, 0, 0, 0);
  return next.toISOString().slice(0, 16);
}

function errorText(error: unknown): string {
  if (error instanceof ApiError) {
    return error.body;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Simulation failed.";
}

function predictionScoreReasonCodes(result?: EventSimulationResponse): string[] {
  const impactRoot = result?.prediction_explanation_json?.impact;
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

function asPrediction(result?: EventSimulationResponse): EventPredictionResponse | null {
  if (!result) {
    return null;
  }
  return {
    event_id: "simulation",
    predicted_priority: result.predicted_priority,
    priority_confidence: result.priority_confidence,
    road_closure_probability: result.road_closure_probability,
    predicted_road_closure: result.predicted_road_closure,
    estimated_clearance_minutes: result.estimated_clearance_minutes,
    clearance_prediction_method: result.clearance_prediction_method,
    clearance_confidence: result.clearance_confidence,
    clearance_confidence_note: result.clearance_confidence_note,
    historical_clearance_range_min: result.historical_clearance_range_min,
    historical_clearance_range_max: result.historical_clearance_range_max,
    estimated_impact_score: result.estimated_impact_score,
    impact_category: result.impact_category,
    impact_radius_km: result.impact_radius_km,
    vehicle_impact_factor: result.vehicle_impact_factor,
    vehicle_impact_note: result.vehicle_impact_note,
    baseline_risk_score: result.counterfactual.baseline_risk_score,
    additional_event_delta: result.counterfactual.additional_event_delta,
    weather_adjustment_json: result.weather_adjustment,
    multi_event_conflict_json: null,
    prediction_explanation_json: result.prediction_explanation_json,
    model_version: null
  };
}

export default function SimulationPage() {
  const { user, ready: authReady } = useFirebaseAuthState();
  const [eventType, setEventType] = useState<EventSimulationRequest["event_type"]>("planned");
  const [eventCause, setEventCause] = useState("sports_event");
  const [latitude, setLatitude] = useState("12.9716");
  const [longitude, setLongitude] = useState("77.5946");
  const [corridor, setCorridor] = useState("Central Spine");
  const [policeStation, setPoliceStation] = useState("Ashok Nagar");
  const [junction, setJunction] = useState("MG Road");
  const [startDatetime, setStartDatetime] = useState(tomorrowIsoHour());
  const [duration, setDuration] = useState("90");
  const [crowdSize, setCrowdSize] = useState("2500");
  const [availableOfficers, setAvailableOfficers] = useState("12");
  const [weatherCondition, setWeatherCondition] = useState<WeatherCondition>("clear");
  const [visibilityM, setVisibilityM] = useState("5000");
  const [description, setDescription] = useState("Planned crowd movement with expected parking spillover near the junction.");

  const simulationMutation = useMutation<EventSimulationResponse, unknown, EventSimulationRequest>({
    mutationFn: (payload) => simulateEvent(payload)
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user) {
      return;
    }
    simulationMutation.mutate({
      event_type: eventType,
      event_cause: eventCause,
      latitude: Number(latitude),
      longitude: Number(longitude),
      corridor,
      police_station: policeStation,
      junction,
      start_datetime: new Date(startDatetime).toISOString(),
      expected_duration_minutes: Number(duration),
      expected_crowd_size: Number(crowdSize),
      available_officers: Number(availableOfficers),
      weather_condition: weatherCondition,
      visibility_m: Number(visibilityM),
      description
    });
  }

  const result = simulationMutation.data;
  const prediction = useMemo(() => asPrediction(result), [result]);
  const scoreReasonCodes = useMemo(() => predictionScoreReasonCodes(result), [result]);

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="rounded-[28px] border border-line/80 bg-panel/90 p-8 shadow-panel">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">Simulation</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
                Forecast event impact before deployment.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
                Simulate a planned or unplanned Bengaluru event and generate dataset-backed impact, weather,
                clearance, manpower, barricade, and diversion recommendations.
              </p>
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.4fr_0.6fr]">
          <div className="space-y-5">
            <AuthPanel
              preferredRole="control_room"
              title="Internal simulation sign-in"
              note="Simulation is a protected internal workflow. Sign in with an admin, control-room, or allowed officer account before generating plans."
            />

            <form onSubmit={handleSubmit} className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Inputs</p>
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <Select label="Event type" value={eventType} onChange={(value) => setEventType(value as EventSimulationRequest["event_type"])} options={["planned", "unplanned"]} />
                <Field label="Event cause" value={eventCause} onChange={setEventCause} />
                <Field label="Latitude" value={latitude} onChange={setLatitude} />
                <Field label="Longitude" value={longitude} onChange={setLongitude} />
                <Field label="Corridor" value={corridor} onChange={setCorridor} />
                <Field label="Police station" value={policeStation} onChange={setPoliceStation} />
                <Field label="Junction" value={junction} onChange={setJunction} />
                <label className="text-sm text-muted">
                  <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Start time</span>
                  <input
                    type="datetime-local"
                    value={startDatetime}
                    onChange={(event) => setStartDatetime(event.target.value)}
                    className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                  />
                </label>
                <Field label="Duration minutes" value={duration} onChange={setDuration} />
                <Field label="Crowd size" value={crowdSize} onChange={setCrowdSize} />
                <Field label="Available officers" value={availableOfficers} onChange={setAvailableOfficers} />
                <Select
                  label="Weather"
                  value={weatherCondition}
                  onChange={(value) => setWeatherCondition(value as WeatherCondition)}
                  options={["clear", "cloudy", "light_rain", "rain", "heavy_rain"]}
                />
                <Field label="Visibility meters" value={visibilityM} onChange={setVisibilityM} />
                <label className="text-sm text-muted md:col-span-2">
                  <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Description</span>
                  <textarea
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    rows={4}
                    className="w-full resize-none rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                  />
                </label>
              </div>
              <button
                type="submit"
                disabled={simulationMutation.isPending || !user}
                className="mt-5 rounded-2xl border border-accent/50 bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
              >
                {simulationMutation.isPending ? "Simulating" : "Run simulation"}
              </button>
              {!authReady ? <p className="mt-4 text-sm text-muted">Restoring internal session...</p> : null}
              {authReady && !user ? <p className="mt-4 text-sm text-muted">Sign in first to run protected simulations.</p> : null}
              {simulationMutation.isError ? (
                <p className="mt-4 text-sm leading-7 text-danger">{errorText(simulationMutation.error)}</p>
              ) : null}
            </form>
          </div>

          <div className="space-y-5">
            {simulationMutation.isPending ? (
              <section className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel space-y-5 animate-pulse">
                <div className="h-3 w-32 rounded bg-line/50" />
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="rounded-2xl border border-line/70 bg-bg/60 p-4 space-y-2">
                      <div className="h-3 w-20 rounded bg-line/50" />
                      <div className="h-5 w-16 rounded bg-line/60" />
                    </div>
                  ))}
                </div>
                <Skeleton.Block height="h-32" />
                <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
                  <Skeleton.Block height="h-48" />
                  <div className="space-y-5">
                    <Skeleton.Block height="h-20" />
                    <Skeleton.Block height="h-20" />
                  </div>
                </div>
              </section>
            ) : !result ? (
              <section className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
                <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Simulation output</p>
                <p className="mt-5 text-sm leading-7 text-muted">
                  Run a simulation to see Event DNA, predicted impact, weather posture, and operational planning panels.
                </p>
              </section>
            ) : (
              <>
                <article className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
                  <div className="mb-4 flex items-center justify-between">
                    <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Simulation summary</p>
                    <p className="text-xs font-semibold text-slate-100 bg-slate-800 px-3 py-1 rounded-md border border-slate-700">Event ID: {result.event_dna.event_id}</p>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                    <Metric label="Predicted priority" value={result.predicted_priority ?? "n/a"} />
                    <Metric label="Impact category" value={result.impact_category ?? "n/a"} />
                    <Metric
                      label="Clearance"
                      value={result.estimated_clearance_minutes ? `${Math.round(result.estimated_clearance_minutes)} min` : "n/a"}
                    />
                    <Metric label="Top similar event" value={result.similar_event_summary.top_match_event_id ?? "n/a"} />
                  </div>
                </article>

                <EventDNACard eventDna={result.event_dna} />

                <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
                  <ImpactScorePanel
                    estimatedImpactScore={result.estimated_impact_score}
                    impactCategory={result.impact_category}
                    impactRadiusKm={result.impact_radius_km}
                    vehicleImpactFactor={result.vehicle_impact_factor}
                    vehicleImpactNote={result.vehicle_impact_note}
                    priorityConfidence={result.priority_confidence}
                    roadClosureProbability={result.road_closure_probability}
                    scoreReasonCodes={scoreReasonCodes}
                  />
                  <div className="grid gap-5">
                    <CounterfactualImpactCard
                      baselineRiskScore={result.counterfactual.baseline_risk_score}
                      eventImpactScore={result.counterfactual.event_impact_score}
                      additionalEventDelta={result.counterfactual.additional_event_delta}
                      honestyNote={result.counterfactual.honesty_note}
                    />
                    <WeatherRiskPanel weatherRisk={result.weather_adjustment} />
                  </div>
                </div>

                <div className="grid gap-5 xl:grid-cols-2">
                  <ManpowerPlanPanel manpower={result.recommendations.manpower} />
                  <BarricadePlanPanel barricades={result.recommendations.barricades} />
                  <DiversionPlanPanel diversions={result.recommendations.diversions} />
                  <EmergencyCorridorPanel emergencyCorridor={result.recommendations.emergency_corridor} />
                  <FlipkartLogisticsImpactPanel logisticsImpact={result.recommendations.flipkart_logistics_impact} />
                  <ActionConfidenceLedger items={result.recommendations.action_confidence_ledger} />
                </div>
              </>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="text-sm text-muted">
      <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
      />
    </label>
  );
}

function Select({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <label className="text-sm text-muted">
      <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
      >
        {options.map((option) => (
          <option key={option} value={option}>{option.replaceAll("_", " ")}</option>
        ))}
      </select>
    </label>
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

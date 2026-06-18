"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import {
  ApiError,
  simulateEvent,
  type EventSimulationRequest,
  type EventSimulationResponse
} from "@/lib/api";
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
            <nav className="flex flex-wrap gap-3">
              <Link href="/command-center" className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy">
                Command center
              </Link>
              <Link href="/map-intelligence" className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy">
                Map intelligence
              </Link>
            </nav>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.44fr_0.56fr]">
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

          <section className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
            <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Simulation output</p>
            {!result ? (
              <p className="mt-5 text-sm leading-7 text-muted">
                Run a simulation to see predicted priority, estimated clearance, weather adjustment, and recommended field actions.
              </p>
            ) : (
              <div className="mt-5 space-y-5">
                <div className="grid gap-3 sm:grid-cols-2">
                  <Metric label="Predicted priority" value={result.predicted_priority ?? "n/a"} />
                  <Metric label="Impact" value={result.impact_category ?? "n/a"} />
                  <Metric label="Score" value={result.estimated_impact_score?.toFixed(1) ?? "n/a"} />
                  <Metric label="Clearance" value={result.estimated_clearance_minutes ? `${Math.round(result.estimated_clearance_minutes)} min` : "n/a"} />
                </div>
                <article className="rounded-2xl border border-line/70 bg-bg/60 p-4">
                  <h2 className="text-lg font-semibold">Event DNA</h2>
                  <p className="mt-3 text-sm leading-7 text-muted">{result.event_dna.dna_summary}</p>
                </article>
                <article className="rounded-2xl border border-line/70 bg-bg/60 p-4">
                  <h2 className="text-lg font-semibold">Recommended action</h2>
                  <p className="mt-3 text-sm leading-7 text-muted">{result.recommendations.recommended_action_summary}</p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <Metric label="Officers" value={String(result.recommendations.manpower.recommended_total_officers)} />
                    <Metric label="Barricades" value={String(result.recommendations.barricades.estimated_units)} />
                  </div>
                </article>
              </div>
            )}
          </section>
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

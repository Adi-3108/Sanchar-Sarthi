"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import {
  getEventDetail,
  getOfficerAssignments,
  submitLiveUpdate,
  type LiveUpdateRequest,
  type LiveUpdateResponse
} from "@/lib/api";
import { useFirebaseAuthState } from "@/lib/auth";
import { useSessionStore } from "@/lib/stores/useSessionStore";

export default function OfficerPage() {
  const queryClient = useQueryClient();
  const session = useSessionStore();
  const { user, ready: authReady } = useFirebaseAuthState();
  const [eventId, setEventId] = useState("");
  const [fieldUpdate, setFieldUpdate] = useState("Crowd spillover near upstream junction");
  const [congestion, setCongestion] = useState<LiveUpdateRequest["current_congestion_level"]>("Warning");
  const [roadClosure, setRoadClosure] = useState(false);
  const [officerShortage, setOfficerShortage] = useState(false);
  const [crowdIncrease, setCrowdIncrease] = useState(true);
  const [rainWaterlogging, setRainWaterlogging] = useState(false);

  const assignmentsQuery = useQuery({
    queryKey: ["officer-assignments"],
    queryFn: getOfficerAssignments,
    enabled: authReady && Boolean(user),
    retry: 1,
    refetchOnWindowFocus: false
  });
  const detailQuery = useQuery({
    queryKey: ["officer-event", eventId],
    queryFn: () => getEventDetail(eventId),
    enabled: authReady && Boolean(user) && eventId.trim().length > 0,
    retry: 1,
    refetchOnWindowFocus: false
  });
  const liveUpdateMutation = useMutation<LiveUpdateResponse, unknown, LiveUpdateRequest>({
    mutationFn: (payload) => submitLiveUpdate(eventId, payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["officer-event", eventId] }),
        queryClient.invalidateQueries({ queryKey: ["officer-assignments"] })
      ]);
    }
  });

  useEffect(() => {
    const firstAssignedEvent = assignmentsQuery.data?.assigned_events[0]?.id;
    if (!eventId && firstAssignedEvent) {
      setEventId(firstAssignedEvent);
    }
  }, [assignmentsQuery.data?.assigned_events, eventId]);

  useEffect(() => {
    if (
      !assignmentsQuery.data ||
      !session.firebaseIdToken ||
      !session.firebaseUid ||
      session.accessLevel !== "police_officer"
    ) {
      return;
    }

    session.setFirebaseSession({
      accessLevel: "police_officer",
      firebaseIdToken: session.firebaseIdToken,
      firebaseUid: session.firebaseUid,
      email: session.email,
      officerId: assignmentsQuery.data.officer_id,
      policeStation: assignmentsQuery.data.police_station,
      assignedCorridors: assignmentsQuery.data.assigned_corridors,
      assignedZones: assignmentsQuery.data.assigned_zones
    });
  }, [
    assignmentsQuery.data,
    session,
    session.accessLevel,
    session.email,
    session.firebaseIdToken,
    session.firebaseUid
  ]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!eventId.trim()) {
      return;
    }

    liveUpdateMutation.mutate({
      current_congestion_level: congestion,
      field_update: fieldUpdate,
      road_closure_active: roadClosure,
      officer_shortage: officerShortage,
      crowd_increase: crowdIncrease,
      rain_waterlogging: rainWaterlogging,
      new_nearby_incident: false
    });
  }

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="rounded-[28px] border border-line/80 bg-panel/90 p-8 shadow-panel">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">Level 2</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">Registered officer field portal.</h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
                Officers can load assignment scope, inspect event dossiers, and submit live escalation signals. The backend still checks
                Firebase identity and event assignment before accepting protected updates.
              </p>
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.36fr_0.64fr]">
          <AuthPanel
            preferredRole="police_officer"
            title="Officer Firebase sign-in"
            note="Use a registered officer account. UI role selection is only a hint; backend assignment checks decide access."
          />

          <div className="grid gap-5">
            <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
              <div className="grid gap-3 md:grid-cols-3">
                <Metric label="Officer ID" value={assignmentsQuery.data?.officer_id ?? "n/a"} />
                <Metric label="Station" value={assignmentsQuery.data?.police_station ?? "n/a"} />
                <Metric label="Assigned events" value={String(assignmentsQuery.data?.assigned_events.length ?? 0)} />
              </div>
              <label className="mt-5 block text-sm text-muted">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Event ID</span>
                <input
                  value={eventId}
                  onChange={(event) => setEventId(event.target.value)}
                  className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                />
              </label>
              {assignmentsQuery.data?.assigned_events.length ? (
                <div className="mt-5 grid gap-3">
                  {assignmentsQuery.data.assigned_events.map((event) => (
                    <button
                      key={event.id}
                      type="button"
                      onClick={() => setEventId(event.id)}
                      className={`rounded-2xl border p-4 text-left transition ${
                        eventId === event.id
                          ? "border-accent/60 bg-accent/10"
                          : "border-line/70 bg-bg/60 hover:border-accent/40"
                      }`}
                    >
                      <p className="text-sm font-semibold text-copy">{event.id}</p>
                      <p className="mt-1 text-sm text-muted">
                        {event.event_cause_clean ?? "Unknown cause"} - {event.corridor ?? "No corridor"}
                      </p>
                    </button>
                  ))}
                </div>
              ) : null}
              <div className="mt-5 grid gap-3 md:grid-cols-3">
                <Metric label="Priority" value={detailQuery.data?.event.priority ?? "n/a"} />
                <Metric label="Corridor" value={detailQuery.data?.event.corridor ?? "n/a"} />
                <Metric label="Impact" value={detailQuery.data?.prediction?.impact_category ?? "n/a"} />
              </div>
              {!authReady ? <p className="mt-4 text-sm text-muted">Restoring officer session...</p> : null}
              {authReady && !user ? (
                <p className="mt-4 text-sm leading-7 text-muted">Sign in with a registered Level 2 account to load assignments.</p>
              ) : null}
              {assignmentsQuery.isError ? (
                <p className="mt-4 text-sm leading-7 text-danger">
                  Officer assignments could not be loaded. Check Firebase role mapping and backend officer profile data.
                </p>
              ) : null}
              {detailQuery.isError ? (
                <p className="mt-4 text-sm leading-7 text-danger">
                  Event detail requires a valid officer or admin Firebase session and matching assignment.
                </p>
              ) : null}
            </article>

            <form onSubmit={handleSubmit} className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Live escalation</p>
              <h2 className="mt-2 text-2xl font-semibold">Submit field update</h2>
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <label className="text-sm text-muted">
                  <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Congestion</span>
                  <select
                    value={congestion}
                    onChange={(event) => setCongestion(event.target.value as LiveUpdateRequest["current_congestion_level"])}
                    className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                  >
                    {["Info", "Watch", "Stable", "Warning", "Critical"].map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                </label>
                <label className="text-sm text-muted md:col-span-2">
                  <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Field update</span>
                  <textarea
                    value={fieldUpdate}
                    onChange={(event) => setFieldUpdate(event.target.value)}
                    rows={4}
                    className="w-full resize-none rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                  />
                </label>
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <Toggle label="Road closure active" checked={roadClosure} onChange={setRoadClosure} />
                <Toggle label="Officer shortage" checked={officerShortage} onChange={setOfficerShortage} />
                <Toggle label="Crowd increasing" checked={crowdIncrease} onChange={setCrowdIncrease} />
                <Toggle label="Rain or waterlogging" checked={rainWaterlogging} onChange={setRainWaterlogging} />
              </div>
              <button
                type="submit"
                disabled={liveUpdateMutation.isPending || !eventId.trim() || !user}
                className="mt-5 rounded-2xl border border-accent/50 bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
              >
                {liveUpdateMutation.isPending ? "Submitting" : "Submit live update"}
              </button>
              {liveUpdateMutation.data ? (
                <div className="mt-5 rounded-2xl border border-ok/30 bg-ok/10 p-4 text-sm leading-7 text-ok">
                  Current score {liveUpdateMutation.data.current_impact_score.toFixed(1)}; alert {liveUpdateMutation.data.alert_level}.
                </div>
              ) : null}
              {liveUpdateMutation.isError ? (
                <p className="mt-4 text-sm leading-7 text-danger">Live update was not accepted. Check Firebase role and event assignment.</p>
              ) : null}
            </form>
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

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label className="flex items-center justify-between gap-4 rounded-2xl border border-line/70 bg-bg/60 p-4 text-sm text-muted">
      <span>{label}</span>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
    </label>
  );
}

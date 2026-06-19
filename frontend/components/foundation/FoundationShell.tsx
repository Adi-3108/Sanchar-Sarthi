"use client";

import Link from "next/link";
import { type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import {
  ApiError,
  createFoundationOfficialIncident,
  createFoundationReport,
  getFoundationControlRoom,
  getFoundationIncidents,
  seedFoundationData,
  transitionFoundationIncidentStatus,
  voteFoundationIncident,
  type FoundationBrowseResponse,
  type FoundationIncident,
  type FoundationIncidentCreateRequest,
  type FoundationStatusTransitionRequest
} from "@/lib/api";
import { useFirebaseAuthState } from "@/lib/auth";
import { type AppLanguage, languageOptions } from "@/lib/i18n";

type Mode = "user" | "control" | "admin";
type Panel = "overview" | "report" | "official";

type Labels = {
  app: string;
  dept: string;
  user: string;
  control: string;
  admin: string;
  active: string;
  reports: string;
  map: string;
  stations: string;
  routes: string;
  report: string;
  official: string;
  overview: string;
  submit: string;
  useLocation: string;
  voteTrue: string;
  voteFalse: string;
  approve: string;
  reject: string;
  activate: string;
  resolve: string;
  status: string;
  severity: string;
  confidence: string;
  station: string;
  contact: string;
  impact: string;
  time: string;
  source: string;
  noIncidents: string;
  loginNote: string;
  protectedTitle: string;
  protectedNote: string;
  citizenTitle: string;
  citizenNote: string;
  routeNote: string;
  hotspot: string;
  viewRoutes: string;
  seed: string;
  seedDone: string;
  reportDone: string;
  officialDone: string;
  gpsOk: string;
  gpsFail: string;
};

const labelsByLanguage: Record<AppLanguage, Labels> = {
  en: {
    app: "Sanchar Sarthi",
    dept: "Bengaluru Traffic Incident Response System",
    user: "User mode",
    control: "Control room",
    admin: "Admin",
    active: "Active incidents",
    reports: "User reported incidents",
    map: "Bengaluru incident map",
    stations: "Station mapping",
    routes: "Route advisory",
    report: "Report incident",
    official: "Official incident",
    overview: "Overview",
    submit: "Submit",
    useLocation: "Use my location",
    voteTrue: "Vote true",
    voteFalse: "Vote false",
    approve: "Approve",
    reject: "Reject",
    activate: "Activate",
    resolve: "Resolve",
    status: "Status",
    severity: "Severity",
    confidence: "Confidence",
    station: "Station",
    contact: "Contact",
    impact: "Route impact",
    time: "Time",
    source: "Source",
    noIncidents: "No incidents here right now.",
    loginNote: "Login is required for reporting and voting.",
    protectedTitle: "Protected operational access",
    protectedNote: "Sign in with a registered account to access control-room and admin actions.",
    citizenTitle: "Citizen sign-in",
    citizenNote: "Signed-in citizens can report incidents and vote on pending reports.",
    routeNote: "This route module is advisory-focused and ready to connect to a live routing provider later.",
    hotspot: "Hotspot",
    viewRoutes: "View alternate routes",
    seed: "Seed foundation data",
    seedDone: "Foundation data seeded successfully.",
    reportDone: "Incident reported successfully.",
    officialDone: "Official incident created successfully.",
    gpsOk: "Device location captured.",
    gpsFail: "Could not fetch device location. Please enter the coordinates manually."
  },
  hi: {
    app: "Sanchar Sarthi",
    dept: "Bengaluru Traffic Incident Response System",
    user: "User mode",
    control: "Control room",
    admin: "Admin",
    active: "Active incidents",
    reports: "User reported incidents",
    map: "Bengaluru incident map",
    stations: "Station mapping",
    routes: "Route advisory",
    report: "Report incident",
    official: "Official incident",
    overview: "Overview",
    submit: "Submit",
    useLocation: "Use my location",
    voteTrue: "Vote true",
    voteFalse: "Vote false",
    approve: "Approve",
    reject: "Reject",
    activate: "Activate",
    resolve: "Resolve",
    status: "Status",
    severity: "Severity",
    confidence: "Confidence",
    station: "Station",
    contact: "Contact",
    impact: "Route impact",
    time: "Time",
    source: "Source",
    noIncidents: "No incidents here right now.",
    loginNote: "Login is required for reporting and voting.",
    protectedTitle: "Protected operational access",
    protectedNote: "Sign in with a registered account to access control-room and admin actions.",
    citizenTitle: "Citizen sign-in",
    citizenNote: "Signed-in citizens can report incidents and vote on pending reports.",
    routeNote: "This route module is advisory-focused and ready to connect to a live routing provider later.",
    hotspot: "Hotspot",
    viewRoutes: "View alternate routes",
    seed: "Seed foundation data",
    seedDone: "Foundation data seeded successfully.",
    reportDone: "Incident reported successfully.",
    officialDone: "Official incident created successfully.",
    gpsOk: "Device location captured.",
    gpsFail: "Could not fetch device location. Please enter the coordinates manually."
  },
  kn: {
    app: "Sanchar Sarthi",
    dept: "Bengaluru Traffic Incident Response System",
    user: "User mode",
    control: "Control room",
    admin: "Admin",
    active: "Active incidents",
    reports: "User reported incidents",
    map: "Bengaluru incident map",
    stations: "Station mapping",
    routes: "Route advisory",
    report: "Report incident",
    official: "Official incident",
    overview: "Overview",
    submit: "Submit",
    useLocation: "Use my location",
    voteTrue: "Vote true",
    voteFalse: "Vote false",
    approve: "Approve",
    reject: "Reject",
    activate: "Activate",
    resolve: "Resolve",
    status: "Status",
    severity: "Severity",
    confidence: "Confidence",
    station: "Station",
    contact: "Contact",
    impact: "Route impact",
    time: "Time",
    source: "Source",
    noIncidents: "No incidents here right now.",
    loginNote: "Login is required for reporting and voting.",
    protectedTitle: "Protected operational access",
    protectedNote: "Sign in with a registered account to access control-room and admin actions.",
    citizenTitle: "Citizen sign-in",
    citizenNote: "Signed-in citizens can report incidents and vote on pending reports.",
    routeNote: "This route module is advisory-focused and ready to connect to a live routing provider later.",
    hotspot: "Hotspot",
    viewRoutes: "View alternate routes",
    seed: "Seed foundation data",
    seedDone: "Foundation data seeded successfully.",
    reportDone: "Incident reported successfully.",
    officialDone: "Official incident created successfully.",
    gpsOk: "Device location captured.",
    gpsFail: "Could not fetch device location. Please enter the coordinates manually."
  }
};

const emptyDraft: FoundationIncidentCreateRequest = {
  incident_type: "roadblock",
  title: "",
  description: "",
  severity: "medium",
  location_name: "",
  latitude: 12.9716,
  longitude: 77.5946,
  locality: "",
  ward: ""
};

function errorText(error: unknown): string {
  if (error instanceof ApiError) {
    return error.body;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Action failed.";
}

function formatTime(value?: string | null): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

function pretty(value: string): string {
  return value.split(/[_-]+/).map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

function cleanDraft(draft: FoundationIncidentCreateRequest): FoundationIncidentCreateRequest {
  return {
    ...draft,
    title: draft.title.trim(),
    description: draft.description.trim(),
    location_name: draft.location_name.trim(),
    locality: draft.locality?.trim() || null,
    ward: draft.ward?.trim() || null
  };
}

type Bounds = { minLat: number; maxLat: number; minLng: number; maxLng: number };

function getBounds(data?: FoundationBrowseResponse): Bounds {
  const points = [
    ...(data?.incidents ?? []).map((incident) => [incident.latitude, incident.longitude] as const),
    ...(data?.stations ?? []).map((station) => [station.latitude, station.longitude] as const),
    ...(data?.hotspots ?? []).map((hotspot) => [hotspot.latitude, hotspot.longitude] as const)
  ];
  if (!points.length) {
    return { minLat: 12.85, maxLat: 13.08, minLng: 77.48, maxLng: 77.7 };
  }
  const lats = points.map(([lat]) => lat);
  const lngs = points.map(([, lng]) => lng);
  return {
    minLat: Math.min(...lats) - 0.02,
    maxLat: Math.max(...lats) + 0.02,
    minLng: Math.min(...lngs) - 0.02,
    maxLng: Math.max(...lngs) + 0.02
  };
}

function pointStyle(bounds: Bounds, latitude: number, longitude: number) {
  const latRange = bounds.maxLat - bounds.minLat || 0.01;
  const lngRange = bounds.maxLng - bounds.minLng || 0.01;
  return {
    top: `${10 + ((bounds.maxLat - latitude) / latRange) * 78}%`,
    left: `${8 + ((longitude - bounds.minLng) / lngRange) * 84}%`
  };
}

function altRoutes(incident: FoundationIncident): string[] {
  const area = incident.locality ?? incident.location_name;
  return [
    `Keep through-traffic away from ${area} and move vehicles through adjacent junction bypasses.`,
    `Protect emergency and bus flow first near ${incident.location_name}.`,
    incident.route_impact_summary ?? `Expect delays near ${incident.location_name}.`
  ];
}

export function FoundationShell({ mode, initialPanel = "overview" }: { mode: Mode; initialPanel?: Panel }) {
  const queryClient = useQueryClient();
  const { user, ready } = useFirebaseAuthState();
  const [language, setLanguage] = useState<AppLanguage>("en");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [panel, setPanel] = useState<Panel>(initialPanel);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [reportDraft, setReportDraft] = useState<FoundationIncidentCreateRequest>(emptyDraft);
  const [officialDraft, setOfficialDraft] = useState<FoundationIncidentCreateRequest>({ ...emptyDraft, incident_type: "road_accident", severity: "high" });
  const [locationMessage, setLocationMessage] = useState<string | null>(null);
  const labels = labelsByLanguage[language];
  const protectedMode = mode !== "user";
  const canManage = mode !== "user";

  const query = useQuery({
    queryKey: [mode === "user" ? "foundation-public" : "foundation-control"],
    queryFn: mode === "user" ? getFoundationIncidents : getFoundationControlRoom,
    enabled: !protectedMode || (ready && Boolean(user)),
    retry: 1,
    refetchOnWindowFocus: false
  });

  async function syncData() {
    await queryClient.invalidateQueries({ queryKey: ["foundation-public"] });
    await queryClient.invalidateQueries({ queryKey: ["foundation-control"] });
  }

  const reportMutation = useMutation({
    mutationFn: (payload: FoundationIncidentCreateRequest) => createFoundationReport(payload),
    onSuccess: async (incident) => {
      setSelectedIncidentId(incident.id);
      setReportDraft(emptyDraft);
      setPanel("overview");
      await syncData();
    }
  });

  const officialMutation = useMutation({
    mutationFn: (payload: FoundationIncidentCreateRequest) => createFoundationOfficialIncident(payload),
    onSuccess: async (incident) => {
      setSelectedIncidentId(incident.id);
      setOfficialDraft({ ...emptyDraft, incident_type: "road_accident", severity: "high" });
      setPanel("overview");
      await syncData();
    }
  });

  const voteMutation = useMutation({
    mutationFn: ({ incidentId, voteValue }: { incidentId: string; voteValue: "true" | "false" }) => voteFoundationIncident(incidentId, voteValue),
    onSuccess: async (incident) => {
      setSelectedIncidentId(incident.id);
      await syncData();
    }
  });

  const statusMutation = useMutation({
    mutationFn: ({ incidentId, payload }: { incidentId: string; payload: FoundationStatusTransitionRequest }) => transitionFoundationIncidentStatus(incidentId, payload),
    onSuccess: async (incident) => {
      setSelectedIncidentId(incident.id);
      await syncData();
    }
  });

  const seedMutation = useMutation({
    mutationFn: () => seedFoundationData(),
    onSuccess: syncData
  });

  const data = query.data;
  const incidents = data?.incidents ?? [];
  const activeIncidents = incidents.filter((incident) => ["active", "escalated", "resolved"].includes(incident.status));
  const reportedIncidents = incidents.filter((incident) => ["reported", "pending_verification", "rejected"].includes(incident.status));
  const selectedIncident = incidents.find((incident) => incident.id === selectedIncidentId) ?? activeIncidents[0] ?? reportedIncidents[0] ?? incidents[0] ?? null;
  const bounds = useMemo(() => getBounds(data), [data]);

  useEffect(() => {
    if (!selectedIncidentId && selectedIncident) {
      setSelectedIncidentId(selectedIncident.id);
    }
  }, [selectedIncident, selectedIncidentId]);

  if (protectedMode && ready && !user) {
    return (
      <main className="min-h-screen bg-slate-100 text-slate-900">
        <div className="mx-auto grid max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[1.2fr_420px]">
          <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-blue-700">{labels.dept}</p>
            <h1 className="mt-3 text-4xl font-bold">{mode === "admin" ? labels.admin : labels.control}</h1>
            <p className="mt-4 text-slate-600">{labels.protectedNote}</p>
          </section>
          <AuthPanel preferredRole={mode === "admin" ? "admin" : "control_room"} title={labels.protectedTitle} note={labels.protectedNote} />
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <div className="flex items-center gap-3">
            <button className="rounded-2xl border border-slate-200 px-3 py-2 text-sm" onClick={() => setSidebarOpen(!sidebarOpen)} type="button">Menu</button>
            <div>
              <p className="text-xl font-bold text-blue-800">{labels.app}</p>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{labels.dept}</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link className="rounded-2xl border border-slate-200 px-3 py-2 text-sm" href="/user">{labels.user}</Link>
            <Link className="rounded-2xl border border-slate-200 px-3 py-2 text-sm" href="/control-room">{labels.control}</Link>
            <Link className="rounded-2xl border border-slate-200 px-3 py-2 text-sm" href="/admin">{labels.admin}</Link>
            <select className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm" value={language} onChange={(event) => setLanguage(event.target.value as AppLanguage)}>
              {languageOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-5 px-4 py-5 xl:grid-cols-[260px_minmax(0,1fr)_340px]">
        {sidebarOpen ? (
          <aside className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="grid gap-2 text-sm font-medium text-slate-700">
              <Link className="rounded-2xl px-3 py-2 hover:bg-slate-100" href="/user">{labels.user}</Link>
              <Link className="rounded-2xl px-3 py-2 hover:bg-slate-100" href="/control-room">{labels.control}</Link>
              <Link className="rounded-2xl px-3 py-2 hover:bg-slate-100" href="/admin">{labels.admin}</Link>
              <Link className="rounded-2xl px-3 py-2 hover:bg-slate-100" href="/reports">{labels.report}</Link>
            </div>
            <div className="mt-4 rounded-2xl border border-blue-100 bg-blue-50 p-4 text-sm leading-6 text-slate-700">{labels.loginNote}</div>
            {mode === "user" ? <div className="mt-4"><AuthPanel preferredRole="citizen" title={labels.citizenTitle} note={labels.citizenNote} /></div> : null}
          </aside>
        ) : null}

        <section className="grid gap-5">
          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-blue-700">{labels.dept}</p>
                <h1 className="mt-2 text-3xl font-bold">{mode === "admin" ? labels.admin : mode === "control" ? labels.control : labels.user}</h1>
              </div>
              <div className="flex flex-wrap gap-2">
                <SwitchButton active={panel === "overview"} label={labels.overview} onClick={() => setPanel("overview")} />
                {mode === "user" ? <SwitchButton active={panel === "report"} label={labels.report} onClick={() => setPanel("report")} /> : null}
                {canManage ? <SwitchButton active={panel === "official"} label={labels.official} onClick={() => setPanel("official")} /> : null}
                {mode === "admin" ? (
                  <button className="rounded-2xl bg-blue-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" disabled={seedMutation.isPending} onClick={() => seedMutation.mutate()} type="button">
                    {seedMutation.isPending ? "..." : labels.seed}
                  </button>
                ) : null}
              </div>
            </div>
            {seedMutation.isSuccess ? <p className="mt-3 text-sm text-emerald-700">{labels.seedDone}</p> : null}
            {query.isError ? <p className="mt-3 text-sm text-rose-700">{errorText(query.error)}</p> : null}
          </section>

          {panel === "report" ? (
            <IncidentForm
              labels={labels}
              draft={reportDraft}
              setDraft={setReportDraft}
              locationMessage={locationMessage}
              setLocationMessage={setLocationMessage}
              pending={reportMutation.isPending}
              success={reportMutation.isSuccess ? labels.reportDone : null}
              error={reportMutation.isError ? errorText(reportMutation.error) : null}
              disabled={!user}
              submitLabel={labels.submit}
              onSubmit={(event) => {
                event.preventDefault();
                reportMutation.mutate(cleanDraft(reportDraft));
              }}
            />
          ) : null}

          {panel === "official" && canManage ? (
            <IncidentForm
              labels={labels}
              draft={officialDraft}
              setDraft={setOfficialDraft}
              locationMessage={locationMessage}
              setLocationMessage={setLocationMessage}
              pending={officialMutation.isPending}
              success={officialMutation.isSuccess ? labels.officialDone : null}
              error={officialMutation.isError ? errorText(officialMutation.error) : null}
              disabled={!user}
              title={labels.official}
              submitLabel={labels.official}
              onSubmit={(event) => {
                event.preventDefault();
                officialMutation.mutate(cleanDraft(officialDraft));
              }}
            />
          ) : null}

          <div className="grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(300px,0.9fr)]">
            <IncidentList title={labels.active} incidents={activeIncidents} labels={labels} canVote={Boolean(user)} canManage={canManage} selectedIncidentId={selectedIncident?.id ?? null} onSelect={setSelectedIncidentId} onVote={(incidentId, voteValue) => voteMutation.mutate({ incidentId, voteValue })} onStatusChange={(incidentId, payload) => statusMutation.mutate({ incidentId, payload })} />
            <IncidentList title={labels.reports} incidents={reportedIncidents} labels={labels} canVote={Boolean(user)} canManage={canManage} selectedIncidentId={selectedIncident?.id ?? null} onSelect={setSelectedIncidentId} onVote={(incidentId, voteValue) => voteMutation.mutate({ incidentId, voteValue })} onStatusChange={(incidentId, payload) => statusMutation.mutate({ incidentId, payload })} compact />
          </div>

          <MapPanel data={data} bounds={bounds} labels={labels} selectedIncidentId={selectedIncident?.id ?? null} onSelectIncident={setSelectedIncidentId} />
        </section>

        <aside className="grid gap-5">
          <DetailPanel incident={selectedIncident} labels={labels} />
          <RoutePanel incident={selectedIncident} labels={labels} />
          <StationPanel data={data} labels={labels} selectedIncidentId={selectedIncident?.id ?? null} onSelectIncident={setSelectedIncidentId} />
        </aside>
      </div>
    </main>
  );
}

function SwitchButton({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return <button className={`rounded-2xl px-4 py-2 text-sm font-semibold ${active ? "bg-blue-700 text-white" : "border border-slate-200 bg-white text-slate-700"}`} onClick={onClick} type="button">{label}</button>;
}

function IncidentList({ title, incidents, labels, canVote, canManage, selectedIncidentId, onSelect, onVote, onStatusChange, compact = false }: { title: string; incidents: FoundationIncident[]; labels: Labels; canVote: boolean; canManage: boolean; selectedIncidentId: string | null; onSelect: (incidentId: string) => void; onVote: (incidentId: string, voteValue: "true" | "false") => void; onStatusChange: (incidentId: string, payload: FoundationStatusTransitionRequest) => void; compact?: boolean }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-end justify-between gap-3">
        <h2 className="text-xl font-bold">{title}</h2>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{incidents.length}</span>
      </div>
      <div className="mt-4 grid gap-3">
        {incidents.map((incident) => (
          <article key={incident.id} className={`rounded-2xl border p-4 ${selectedIncidentId === incident.id ? "border-blue-600 bg-blue-50" : "border-slate-200 bg-slate-50"}`}>
            <button className="block w-full text-left" onClick={() => onSelect(incident.id)} type="button">
              <div className="flex flex-wrap justify-between gap-3">
                <div>
                  <h3 className="font-bold text-slate-900">{incident.title}</h3>
                  <p className="mt-1 text-sm text-slate-600">{incident.location_name}</p>
                </div>
                <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase text-slate-700">{pretty(incident.severity)}</span>
              </div>
              {!compact ? <p className="mt-3 text-sm leading-6 text-slate-600">{incident.description}</p> : null}
            </button>
            <div className="mt-4 grid gap-2 text-sm md:grid-cols-2">
              <Info label={labels.status} value={pretty(incident.status)} />
              <Info label={labels.time} value={formatTime(incident.created_at)} />
              <Info label={labels.station} value={incident.assigned_station_name ?? "Pending assignment"} />
              <Info label={labels.confidence} value={`${Math.round(incident.confidence_score * 100)}%`} />
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm disabled:opacity-50" disabled={!canVote} onClick={() => onVote(incident.id, "true")} type="button">{labels.voteTrue} ({incident.true_vote_count})</button>
              <button className="rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm disabled:opacity-50" disabled={!canVote} onClick={() => onVote(incident.id, "false")} type="button">{labels.voteFalse} ({incident.false_vote_count})</button>
              <button className="rounded-2xl border border-blue-200 bg-blue-100 px-3 py-2 text-sm font-semibold text-blue-800" onClick={() => onSelect(incident.id)} type="button">{labels.viewRoutes}</button>
            </div>
            {canManage ? <div className="mt-3 flex flex-wrap gap-2"><MiniAction label={labels.approve} onClick={() => onStatusChange(incident.id, { status: "pending_verification" })} /><MiniAction label={labels.reject} onClick={() => onStatusChange(incident.id, { status: "rejected" })} /><MiniAction label={labels.activate} onClick={() => onStatusChange(incident.id, { status: "active" })} /><MiniAction label={labels.resolve} onClick={() => onStatusChange(incident.id, { status: "resolved", resolution_notes: "Resolved from control room." })} /></div> : null}
          </article>
        ))}
        {!incidents.length ? <p className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">{labels.noIncidents}</p> : null}
      </div>
    </section>
  );
}

function MiniAction({ label, onClick }: { label: string; onClick: () => void }) {
  return <button className="rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm" onClick={onClick} type="button">{label}</button>;
}

function MapPanel({ data, bounds, labels, selectedIncidentId, onSelectIncident }: { data?: FoundationBrowseResponse; bounds: Bounds; labels: Labels; selectedIncidentId: string | null; onSelectIncident: (incidentId: string) => void }) {
  const active = (data?.incidents ?? []).filter((incident) => ["active", "escalated", "resolved"].includes(incident.status));
  const pending = (data?.incidents ?? []).filter((incident) => ["reported", "pending_verification", "rejected"].includes(incident.status));
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-xl font-bold">{labels.map}</h2>
      <div className="mt-4 rounded-3xl border border-slate-200 bg-[linear-gradient(180deg,#f8fbff,#e0f2fe)] p-4">
        <div className="relative min-h-[360px] overflow-hidden rounded-[28px] border border-blue-100 bg-[linear-gradient(135deg,#f8fafc,#dbeafe)]">
          <div className="absolute left-5 top-5 rounded-2xl bg-white/90 px-4 py-3 text-xs leading-6 text-slate-600 shadow-sm">
            <p>{labels.active}</p>
            <p>{labels.reports}</p>
            <p>{labels.hotspot}</p>
          </div>
          {active.map((incident) => (
            <button key={incident.id} className={`absolute h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 ${selectedIncidentId === incident.id ? "border-blue-900 bg-blue-700" : "border-blue-200 bg-blue-600"}`} style={pointStyle(bounds, incident.latitude, incident.longitude)} onClick={() => onSelectIncident(incident.id)} type="button" title={incident.title} />
          ))}
          {pending.map((incident) => (
            <button key={incident.id} className="absolute h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-amber-200 bg-amber-500" style={pointStyle(bounds, incident.latitude, incident.longitude)} onClick={() => onSelectIncident(incident.id)} type="button" title={incident.title} />
          ))}
          {(data?.hotspots ?? []).map((hotspot) => <div key={hotspot.hotspot_id} className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full border border-rose-200 bg-rose-500/20 px-3 py-1 text-[11px] font-semibold text-rose-800" style={pointStyle(bounds, hotspot.latitude, hotspot.longitude)}>{hotspot.incident_count}</div>)}
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {(data?.hotspots ?? []).map((hotspot) => <div key={hotspot.hotspot_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm"><p className="font-semibold text-slate-900">{hotspot.label}</p><p className="mt-1 text-slate-600">{hotspot.incident_count} linked incidents</p><p className="mt-1 text-slate-500">{pretty(hotspot.severity)}</p></div>)}
      </div>
    </section>
  );
}

function DetailPanel({ incident, labels }: { incident: FoundationIncident | null; labels: Labels }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-xl font-bold">{incident ? incident.title : labels.active}</h2>
      {!incident ? <p className="mt-4 text-sm text-slate-500">Select an incident from the list or map.</p> : (
        <div className="mt-4 grid gap-4">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm leading-6 text-slate-600">{incident.description}</p>
            <div className="mt-4 grid gap-2 text-sm md:grid-cols-2">
              <Info label={labels.status} value={pretty(incident.status)} />
              <Info label={labels.severity} value={pretty(incident.severity)} />
              <Info label={labels.source} value={pretty(incident.source_type)} />
              <Info label={labels.time} value={formatTime(incident.created_at)} />
              <Info label={labels.station} value={incident.assigned_station_name ?? "Pending assignment"} />
              <Info label={labels.contact} value={incident.station_contact_number ?? incident.assigned_station_code ?? "Not available"} />
              <Info label={labels.confidence} value={`${Math.round(incident.confidence_score * 100)}%`} />
              <Info label={labels.impact} value={incident.route_impact_summary ?? "Under review"} />
            </div>
          </div>
          {incident.latest_prediction ? <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm"><p className="font-semibold text-slate-900">ML and rule output</p><div className="mt-3 grid gap-2 md:grid-cols-2"><Info label={labels.severity} value={pretty(incident.latest_prediction.predicted_severity ?? incident.severity)} /><Info label="Police force" value={String(incident.latest_prediction.police_force_required ?? incident.police_force_required ?? "-")} /><Info label="Barricades" value={String(incident.latest_prediction.barricades_required ?? incident.barricades_required ?? "-")} /><Info label="Urgency" value={incident.latest_prediction.urgency_score !== undefined && incident.latest_prediction.urgency_score !== null ? `${Math.round(incident.latest_prediction.urgency_score * 100)}%` : "-"} /></div></div> : null}
        </div>
      )}
    </section>
  );
}

function RoutePanel({ incident, labels }: { incident: FoundationIncident | null; labels: Labels }) {
  const routes = incident ? altRoutes(incident) : [];
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-xl font-bold">{labels.routes}</h2>
      {!incident ? <p className="mt-4 text-sm text-slate-500">Select an incident to inspect alternate routes.</p> : (
        <div className="mt-4 grid gap-3">{routes.map((route, index) => <div key={`${incident.id}-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600">{route}</div>)}<p className="rounded-2xl bg-blue-50 px-4 py-3 text-sm leading-6 text-blue-900">{labels.routeNote}</p></div>
      )}
    </section>
  );
}

function StationPanel({ data, labels, selectedIncidentId, onSelectIncident }: { data?: FoundationBrowseResponse; labels: Labels; selectedIncidentId: string | null; onSelectIncident: (incidentId: string) => void }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-xl font-bold">{labels.stations}</h2>
      <div className="mt-4 grid gap-3">{(data?.stations ?? []).map((station) => {
        const linked = (data?.incidents ?? []).filter((incident) => incident.assigned_station_name === station.name);
        return <div key={station.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><p className="font-semibold text-slate-900">{station.name}</p><p className="mt-1 text-sm text-slate-600">{station.locality} · {station.station_code}</p><p className="mt-1 text-sm text-slate-600">{labels.contact}: {station.contact_number ?? "Not available"}</p><div className="mt-3 flex flex-wrap gap-2">{linked.slice(0, 3).map((incident) => <button key={incident.id} className={`rounded-full px-3 py-1 text-xs font-medium ${selectedIncidentId === incident.id ? "bg-blue-700 text-white" : "bg-white text-slate-700"}`} onClick={() => onSelectIncident(incident.id)} type="button">{incident.title}</button>)}</div></div>;
      })}</div>
    </section>
  );
}

function IncidentForm({ labels, draft, setDraft, locationMessage, setLocationMessage, pending, success, error, disabled, onSubmit, title, submitLabel }: { labels: Labels; draft: FoundationIncidentCreateRequest; setDraft: (draft: FoundationIncidentCreateRequest) => void; locationMessage: string | null; setLocationMessage: (message: string | null) => void; pending: boolean; success: string | null; error: string | null; disabled: boolean; onSubmit: (event: FormEvent<HTMLFormElement>) => void; title?: string; submitLabel: string }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-2xl font-bold">{title ?? labels.report}</h2>
      <form className="mt-5 grid gap-4 md:grid-cols-2" onSubmit={onSubmit}>
        <Field label="Title"><input className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-slate-900" value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} /></Field>
        <Field label={labels.severity}><select className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900" value={draft.severity} onChange={(event) => setDraft({ ...draft, severity: event.target.value as FoundationIncidentCreateRequest["severity"] })}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select></Field>
        <Field label="Incident type"><select className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900" value={draft.incident_type} onChange={(event) => setDraft({ ...draft, incident_type: event.target.value })}><option value="roadblock">Roadblock</option><option value="road_accident">Road accident</option><option value="signal_failure">Signal failure</option><option value="waterlogging">Waterlogging</option><option value="vip_movement">VIP movement</option><option value="fallen_tree">Fallen tree</option><option value="protest">Protest</option></select></Field>
        <Field label="Location"><input className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-slate-900" value={draft.location_name} onChange={(event) => setDraft({ ...draft, location_name: event.target.value })} /></Field>
        <Field label="Locality"><input className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-slate-900" value={draft.locality ?? ""} onChange={(event) => setDraft({ ...draft, locality: event.target.value })} /></Field>
        <Field label="Ward"><input className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-slate-900" value={draft.ward ?? ""} onChange={(event) => setDraft({ ...draft, ward: event.target.value })} /></Field>
        <Field label="Latitude"><input className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-slate-900" type="number" step="0.0001" value={draft.latitude} onChange={(event) => setDraft({ ...draft, latitude: Number(event.target.value) })} /></Field>
        <Field label="Longitude"><input className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-slate-900" type="number" step="0.0001" value={draft.longitude} onChange={(event) => setDraft({ ...draft, longitude: Number(event.target.value) })} /></Field>
        <div className="md:col-span-2"><Field label="Description"><textarea className="min-h-[120px] w-full rounded-2xl border border-slate-300 px-4 py-3 text-slate-900" value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} /></Field></div>
        <div className="md:col-span-2 flex flex-wrap items-center gap-3">
          <button className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm" onClick={() => fillLocation(draft, setDraft, setLocationMessage, labels)} type="button">{labels.useLocation}</button>
          <button className="rounded-2xl bg-blue-700 px-5 py-3 text-sm font-semibold text-white disabled:opacity-60" disabled={pending || disabled} type="submit">{pending ? "..." : submitLabel}</button>
          {disabled ? <span className="text-sm text-amber-700">{labels.loginNote}</span> : null}
        </div>
        {locationMessage ? <p className="md:col-span-2 text-sm text-slate-600">{locationMessage}</p> : null}
        {success ? <p className="md:col-span-2 text-sm text-emerald-700">{success}</p> : null}
        {error ? <p className="md:col-span-2 text-sm text-rose-700">{error}</p> : null}
      </form>
    </section>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="block text-sm text-slate-600"><span className="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</span>{children}</label>;
}

function Info({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</dt><dd className="mt-1 font-medium text-slate-900">{value}</dd></div>;
}

function fillLocation(draft: FoundationIncidentCreateRequest, setDraft: (draft: FoundationIncidentCreateRequest) => void, setMessage: (message: string | null) => void, labels: Labels) {
  if (!("geolocation" in navigator)) {
    setMessage(labels.gpsFail);
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (position) => {
      setDraft({ ...draft, latitude: Number(position.coords.latitude.toFixed(6)), longitude: Number(position.coords.longitude.toFixed(6)) });
      setMessage(labels.gpsOk);
    },
    () => setMessage(labels.gpsFail),
    { enableHighAccuracy: true, timeout: 12000 }
  );
}

export default FoundationShell;


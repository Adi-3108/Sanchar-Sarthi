"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import { useSessionStore } from "@/lib/stores/useSessionStore";
import { SearchableSelect } from "@/components/layout/SearchableSelect";
import {
  ApiError,
  createOfficer,
  deleteFoundationAdminIncident,
  deleteFoundationAdminVote,
  escalateFoundationAdminIncident,
  generateEventFeatures,
  getFoundationAdminOverview,
  getHealth,
  getMapConfig,
  getModelRuns,
  loadDemoDataset,
  updateFoundationAdminIncident,
  updateFoundationAdminStation,
  updateFoundationAdminUser,
  type CreateControlRoomRequest,
  type CreateControlRoomResponse,
  type CreateOfficerRequest,
  type CreateOfficerResponse,
  type DatasetLoadResponse,
  type FeatureGenerationResponse,
  type FoundationAdminUser,
  type FoundationAuditLog,
  type FoundationIncident,
  type FoundationStation,
  type FoundationVote
} from "@/lib/api";
import { useFirebaseAuthState } from "@/lib/auth";

function metric(value: number | string | undefined): string {
  if (value === undefined || value === null) {
    return "n/a";
  }
  return String(value);
}

function errorText(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.body);
      return parsed.error?.message || error.body;
    } catch {
      return error.body;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Action failed.";
}

function ErrorAlert({ title, error }: { title: string; error: unknown }) {
  if (!error) return null;
  return (
    <div className="mt-4 flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-800 shadow-sm animate-in fade-in zoom-in-95">
      <svg className="mt-0.5 h-5 w-5 shrink-0 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div>
        <h3 className="font-semibold">{title}</h3>
        <p className="mt-1 text-sm text-rose-700/90">{errorText(error)}</p>
      </div>
    </div>
  );
}

function SuccessAlert({ title, message }: { title: string; message: string | null | undefined }) {
  if (!message) return null;
  return (
    <div className="mt-4 flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800 shadow-sm animate-in fade-in zoom-in-95">
      <svg className="mt-0.5 h-5 w-5 shrink-0 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div>
        <h3 className="font-semibold">{title}</h3>
        <p className="mt-1 text-sm text-emerald-700/90">{message}</p>
      </div>
    </div>
  );
}

function splitScope(value: string): string[] {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function pretty(value: string): string {
  return value.split(/[_-]+/).map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

function formatTime(value?: string | null): string {
  if (!value) {
    return "-";
  }
  const utcValue = value.endsWith('Z') ? value : `${value}Z`;
  const date = new Date(utcValue);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function AdminPage() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const { user, ready: authReady } = useFirebaseAuthState();
  const session = useSessionStore();
  const [officerForm, setOfficerForm] = useState<CreateOfficerRequest>({
    email: "officer.demo@sancharsarthi.local",
    password: "Password@123",
    officer_id: "BTP-DEMO-001",
    display_name: "Officer Demo",
    rank: "Traffic Constable",
    police_station: "HSR Layout",
    assigned_corridors: ["ORR East 1"],
    assigned_zones: ["East"]
  });
  const [controlRoomForm, setControlRoomForm] = useState<CreateControlRoomRequest>({
    email: "new.control.room@eventflow.local",
    password: "Password@123",
    display_name: "New Control Room Officer"
  });

  const isAdmin = session.accessLevel === "admin";
  const canRunProtectedActions = authReady && Boolean(user) && isAdmin;

  // Redirect removed so users can see the AuthPanel or Unauthorized message.

  const healthQuery = useQuery({ queryKey: ["admin-health"], queryFn: getHealth, retry: 1, refetchOnWindowFocus: false });
  // Removed stationsQuery
  const modelRunsQuery = useQuery({ queryKey: ["admin-model-runs"], queryFn: getModelRuns, enabled: canRunProtectedActions, retry: 1, refetchOnWindowFocus: false });
  const mapQuery = useQuery({ queryKey: ["admin-map-config"], queryFn: getMapConfig, retry: 1, refetchOnWindowFocus: false });
  const foundationQuery = useQuery({ queryKey: ["foundation-admin-overview"], queryFn: getFoundationAdminOverview, enabled: canRunProtectedActions, retry: 1, refetchOnWindowFocus: false });

  async function refreshAdminData() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["admin-model-runs"] }),
      queryClient.invalidateQueries({ queryKey: ["foundation-admin-overview"] })
    ]);
  }

  const loadDemoMutation = useMutation<DatasetLoadResponse, unknown>({ mutationFn: () => loadDemoDataset(), onSuccess: refreshAdminData });
  const generateFeaturesMutation = useMutation<FeatureGenerationResponse, unknown>({ mutationFn: () => generateEventFeatures(), onSuccess: refreshAdminData });
  const createOfficerMutation = useMutation<CreateOfficerResponse, unknown, CreateOfficerRequest>({ mutationFn: (payload) => createOfficer(payload) });
  // const createControlRoomMutation = useMutation<CreateControlRoomResponse, unknown, CreateControlRoomRequest>({ mutationFn: (payload) => createControlRoomUser(payload) });
  const incidentMutation = useMutation({ mutationFn: ({ incidentId, payload }: { incidentId: string; payload: Parameters<typeof updateFoundationAdminIncident>[1] }) => updateFoundationAdminIncident(incidentId, payload), onSuccess: refreshAdminData });
  const deleteIncidentMutation = useMutation({ mutationFn: (incidentId: string) => deleteFoundationAdminIncident(incidentId), onSuccess: refreshAdminData });
  const escalateMutation = useMutation({ mutationFn: (incidentId: string) => escalateFoundationAdminIncident(incidentId), onSuccess: refreshAdminData });
  const stationMutation = useMutation({ mutationFn: ({ stationId, active }: { stationId: string; active: boolean }) => updateFoundationAdminStation(stationId, { active }), onSuccess: refreshAdminData });
  const userMutation = useMutation({ mutationFn: ({ userId, is_active }: { userId: string; is_active: boolean }) => updateFoundationAdminUser(userId, { is_active }), onSuccess: refreshAdminData });
  const voteMutation = useMutation({ mutationFn: (voteId: string) => deleteFoundationAdminVote(voteId), onSuccess: refreshAdminData });

  const latestRun = modelRunsQuery.data?.model_runs[0];
  const latestAction = useMemo(() => {
    if (createOfficerMutation.data) {
      return `Officer ${createOfficerMutation.data.officer_id} created for Level 2 access.`;
    }
    if (generateFeaturesMutation.data) {
      return generateFeaturesMutation.data.message ?? "Event features generated.";
    }
    if (loadDemoMutation.data) {
      return loadDemoMutation.data.message ?? "Demo dataset loaded.";
    }
    return null;
  }, [createOfficerMutation.data, generateFeaturesMutation.data, loadDemoMutation.data]);

  const stationOptions = useMemo(() => {
    return (foundationQuery.data?.stations || []).map(s => ({ label: s.name, value: s.name }));
  }, [foundationQuery.data?.stations]);

  function updateOfficerField<Key extends keyof CreateOfficerRequest>(key: Key, value: CreateOfficerRequest[Key]) {
    setOfficerForm((current) => ({ ...current, [key]: value }));
  }

  function handleCreateOfficer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createOfficerMutation.mutate({
      ...officerForm,
      assigned_corridors: officerForm.assigned_corridors.filter(Boolean),
      assigned_zones: officerForm.assigned_zones.filter(Boolean)
    });
  }

  // function updateControlRoomField<Key extends keyof CreateControlRoomRequest>(key: Key, value: CreateControlRoomRequest[Key]) {
  //   setControlRoomForm((current) => ({ ...current, [key]: value }));
  // }

  // function handleCreateControlRoom(event: FormEvent<HTMLFormElement>) {
  //   event.preventDefault();
  //   createControlRoomMutation.mutate(controlRoomForm);
  // }

  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);

  const hasAccess = mounted && session.accessLevel === "admin";

  if (!authReady || !user || !hasAccess) {
    return (
      <main className="min-h-screen bg-slate-100 px-6 py-8 text-slate-900 md:px-10">
        <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-[1fr_380px]">
          <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-blue-700">Sanchar Sarthi</p>
            <h1 className="mt-3 text-4xl font-bold">{authReady ? "Admin access is protected." : "Checking admin session."}</h1>
            <p className="mt-4 text-slate-600">Sign in with an admin Firebase account to access incident management, audit logs, model visibility, and system controls.</p>
          </section>
          {authReady && user && !hasAccess ? (
            <div className="rounded-3xl border border-rose-200 bg-rose-50 p-8 shadow-sm flex flex-col justify-center items-center text-center">
              <svg className="h-12 w-12 text-rose-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <h2 className="text-2xl font-bold text-rose-800">User Not Authorized</h2>
              <p className="mt-2 text-rose-700">You do not have the required permissions to access the Admin Portal.</p>
            </div>
          ) : (
            <AuthPanel preferredRole="admin" title="Admin Firebase sign-in" note="Admin mode is not available to public users." />
          )}
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-8 text-slate-900 md:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-semibold uppercase tracking-[0.32em] text-blue-700">Level 1</p>
              <h1 className="mt-3 text-4xl font-bold tracking-tight md:text-5xl">Sanchar Sarthi admin and operations console</h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">This admin surface now covers Phase 3 management for incidents, users, stations, votes, predictions, and audit logs, while keeping the earlier system-health and officer-bootstrap tools available.</p>
            </div>

          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-4">
          <MetricCard label="Backend" value={healthQuery.isLoading ? "Checking" : healthQuery.isError ? "Needs attention" : "Operational"} note={`Database: ${healthQuery.data?.database ?? "n/a"}`} />
          <MetricCard label="Firebase" value={healthQuery.data?.auth.firebase ?? "n/a"} note={`Priority model: ${healthQuery.data?.models.priority ?? "n/a"}`} />
          <MetricCard label="Map provider" value={mapQuery.data?.activeProvider ?? "Checking"} note={`Fallback: ${mapQuery.data?.fallbackProvider ?? "osm"}`} />
          <MetricCard label="Latest model run" value={latestRun?.model_name ?? "No run yet"} note={`Version: ${latestRun?.model_version ?? "n/a"}`} />
        </section>

        <section className="grid gap-5 lg:grid-cols-3">
          <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Foundation summary</p>
                <h2 className="mt-2 text-2xl font-bold">Admin-wide operational snapshot</h2>
              </div>
              <div className="flex flex-wrap gap-3">
                <button type="button" onClick={() => loadDemoMutation.mutate()} disabled={!canRunProtectedActions || loadDemoMutation.isPending} className="rounded-2xl bg-blue-700 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60">{loadDemoMutation.isPending ? "Loading demo dataset" : "Load demo dataset"}</button>
                <button type="button" onClick={() => generateFeaturesMutation.mutate()} disabled={!canRunProtectedActions || generateFeaturesMutation.isPending} className="rounded-2xl border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-700 disabled:opacity-60">{generateFeaturesMutation.isPending ? "Generating features" : "Generate features"}</button>
              </div>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <Metric value={metric(foundationQuery.data?.summary.incident_count)} label="Incidents" />
              <Metric value={metric(foundationQuery.data?.summary.station_count)} label="Stations" />
              <Metric value={metric(foundationQuery.data?.summary.user_count)} label="Users" />
              <Metric value={metric(foundationQuery.data?.summary.vote_count)} label="Votes" />
              <Metric value={metric(foundationQuery.data?.summary.prediction_count)} label="Predictions" />
              <Metric value={metric(foundationQuery.data?.summary.audit_log_count)} label="Audit logs" />
            </div>
            {latestAction ? <p className="mt-4 text-sm leading-7 text-emerald-700">{latestAction}</p> : null}
            {foundationQuery.isError ? <p className="mt-3 text-sm text-rose-700">{errorText(foundationQuery.error)}</p> : null}
          </article>

          <form onSubmit={handleCreateOfficer} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Officer access</p>
            <h2 className="mt-2 text-2xl font-bold">Create registered police officer</h2>
            <div className="mt-5 grid gap-4">
              <Field label="Officer email" value={officerForm.email} onChange={(value) => updateOfficerField("email", value)} />
              <Field label="Password" type="password" value={officerForm.password} onChange={(value) => updateOfficerField("password", value)} />
              <Field label="Officer ID" value={officerForm.officer_id} onChange={(value) => updateOfficerField("officer_id", value)} />
              <Field label="Display name" value={officerForm.display_name} onChange={(value) => updateOfficerField("display_name", value)} />
              <Field label="Rank" value={officerForm.rank ?? ""} onChange={(value) => updateOfficerField("rank", value)} />
              <div className="flex flex-col gap-2 text-sm">
                <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Police station</span>
                <SearchableSelect
                  name="police_station"
                  value={officerForm.police_station}
                  onChange={(value) => updateOfficerField("police_station", value)}
                  options={stationOptions}
                  placeholder="Select police station..."
                  required
                />
              </div>
              <Field label="Assigned corridors" value={officerForm.assigned_corridors.join(", ")} onChange={(value) => updateOfficerField("assigned_corridors", splitScope(value))} />
              <Field label="Assigned zones" value={officerForm.assigned_zones.join(", ")} onChange={(value) => updateOfficerField("assigned_zones", splitScope(value))} />
            </div>
            <button type="submit" disabled={!canRunProtectedActions || createOfficerMutation.isPending} className="mt-5 rounded-2xl bg-blue-700 px-5 py-3 text-sm font-semibold text-white disabled:opacity-60">{createOfficerMutation.isPending ? "Creating officer" : "Create officer"}</button>
            <SuccessAlert title="Officer Created" message={createOfficerMutation.isSuccess && createOfficerMutation.data ? `Officer ${createOfficerMutation.data.officer_id} created successfully.` : null} />
            <ErrorAlert title="Failed to create officer" error={createOfficerMutation.error} />
          </form>

          {/* <form onSubmit={handleCreateControlRoom} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Command Access</p>
            <h2 className="mt-2 text-2xl font-bold">Create control room user</h2>
            <div className="mt-5 grid gap-4">
              <Field label="Email" value={controlRoomForm.email} onChange={(value) => updateControlRoomField("email", value)} />
              <Field label="Password" value={controlRoomForm.password} onChange={(value) => updateControlRoomField("password", value)} />
              <Field label="Display name" value={controlRoomForm.display_name} onChange={(value) => updateControlRoomField("display_name", value)} />
            </div>
            <button type="submit" disabled={!canRunProtectedActions || createControlRoomMutation.isPending} className="mt-5 rounded-2xl bg-blue-700 px-5 py-3 text-sm font-semibold text-white disabled:opacity-60">{createControlRoomMutation.isPending ? "Creating user" : "Create control room user"}</button>
            <SuccessAlert title="User Created" message={createControlRoomMutation.isSuccess && createControlRoomMutation.data ? `Control Room user created! Firebase UID: ${createControlRoomMutation.data.firebase_uid}` : null} />
            <ErrorAlert title="Failed to create control room user" error={createControlRoomMutation.error} />
          </form> */}
        </section>

        <section className="grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
          <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Incident management</p>
                <h2 className="mt-2 text-2xl font-bold">Admin incident controls</h2>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{foundationQuery.data?.incidents.length ?? 0}</span>
            </div>
            <div className="mt-4 grid gap-3">
              {escalateMutation.isSuccess && escalateMutation.data && (
                <div className="mb-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
                  <p className="text-sm font-semibold text-emerald-800">✅ Incident escalated successfully!</p>
                  <p className="mt-1 text-sm text-emerald-700">
                    New Event ID: <span className="font-mono font-bold">{escalateMutation.data.event_id}</span>
                  </p>
                  <p className="mt-1 text-xs text-emerald-600">AI prediction and recommendations have been generated. You can now generate a Post-Event Report using this Event ID.</p>
                </div>
              )}
              {escalateMutation.isError && (
                <div className="mb-3 rounded-2xl border border-rose-200 bg-rose-50 p-4">
                  <p className="text-sm font-semibold text-rose-800">Failed to escalate incident</p>
                  <p className="mt-1 text-xs text-rose-700">{errorText(escalateMutation.error)}</p>
                </div>
              )}
              {(foundationQuery.data?.incidents ?? [])
                .filter(incident => !["resolved", "archived", "rejected"].includes(incident.status))
                .slice(0, 8)
                .map((incident) => (
                <IncidentCard
                  key={incident.id}
                  incident={incident}
                  isEscalating={escalateMutation.isPending}
                  onActivate={() => incidentMutation.mutate({ incidentId: incident.id, payload: { status: "active" } })}
                  onResolve={() => incidentMutation.mutate({ incidentId: incident.id, payload: { status: "resolved", resolution_notes: "Resolved from admin console." } })}
                  onArchive={() => incidentMutation.mutate({ incidentId: incident.id, payload: { status: "archived", visible_to_public: false } })}
                  onDelete={() => deleteIncidentMutation.mutate(incident.id)}
                  onEscalate={() => { escalateMutation.reset(); escalateMutation.mutate(incident.id); }}
                />
              ))}
            </div>
          </article>

          <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Status distribution</p>
            <h2 className="mt-2 text-2xl font-bold">Lifecycle mix</h2>
            <div className="mt-4 grid gap-3">
              {Object.entries((foundationQuery.data?.summary.status_counts ?? {}) as Record<string, number>).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
                  <span className="font-medium text-slate-700">{pretty(status)}</span>
                  <span className="font-semibold text-slate-900">{count}</span>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="grid gap-5 xl:grid-cols-2">
          <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Stations</p>
            <h2 className="mt-2 text-2xl font-bold">Station controls</h2>
            <div className="mt-4 grid gap-3">
              {(foundationQuery.data?.stations ?? []).map((station: FoundationStation) => (
                <div key={station.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-900">{station.name}</p>
                      <p className="mt-1 text-sm text-slate-600">{station.locality} · {station.station_code}</p>
                      <p className="mt-1 text-sm text-slate-600">{station.contact_number ?? "Contact unavailable"}</p>
                    </div>
                    <button type="button" onClick={() => stationMutation.mutate({ stationId: station.id, active: !station.active })} className="rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700">{station.active ? "Disable" : "Enable"}</button>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Users</p>
            <h2 className="mt-2 text-2xl font-bold">User access</h2>
            <div className="mt-4 grid gap-3">
              {(foundationQuery.data?.users ?? []).slice(0, 8).map((account: FoundationAdminUser) => (
                <div key={account.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-900">{account.display_name ?? account.auth_provider_uid}</p>
                      <p className="mt-1 text-sm text-slate-600">{pretty(account.role)}</p>
                      <p className="mt-1 text-sm text-slate-600">Created: {formatTime(account.created_at)}</p>
                    </div>
                    <button type="button" onClick={() => userMutation.mutate({ userId: account.id, is_active: !account.is_active })} className="rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700">{account.is_active ? "Disable" : "Enable"}</button>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="grid gap-5 xl:grid-cols-2">
          <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Votes</p>
            <h2 className="mt-2 text-2xl font-bold">Vote audit and cleanup</h2>
            <div className="mt-4 grid gap-3">
              {(foundationQuery.data?.votes ?? []).slice(0, 10).map((vote: FoundationVote) => (
                <div key={vote.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
                  <div>
                    <p className="font-medium text-slate-900">Incident {vote.incident_id}</p>
                    <p className="text-slate-600">{vote.vote_value.toUpperCase()} · {formatTime(vote.created_at)}</p>
                  </div>
                  <button type="button" onClick={() => voteMutation.mutate(vote.id)} className="rounded-2xl border border-rose-200 bg-white px-3 py-2 text-sm text-rose-700">Delete vote</button>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Audit logs</p>
            <h2 className="mt-2 text-2xl font-bold">Recent administrative actions</h2>
            <div className="mt-4 grid gap-3">
              {(foundationQuery.data?.logs ?? []).slice(0, 12).map((log: FoundationAuditLog) => (
                <div key={log.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-900">{pretty(log.action)}</p>
                      <p className="mt-1 text-slate-600">{pretty(log.actor_role)} · {formatTime(log.created_at)}</p>
                    </div>
                    <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">{log.resource_type}</span>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>
      </div>

      {/* createControlRoomMutation.isSuccess && createControlRoomMutation.data && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
              <svg className="h-6 w-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="mt-4 text-center text-xl font-bold text-slate-900">User Created</h3>
            <p className="mt-2 text-center text-sm leading-6 text-slate-600">
              Control Room user has been created successfully. They can now log in using the password you provided.
            </p>
            <div className="mt-6 flex justify-center">
              <button
                onClick={() => {
                  createControlRoomMutation.reset();
                  setControlRoomForm({
                    email: "new.control.room@eventflow.local",
                    password: "Password@123",
                    display_name: "New Control Room Officer"
                  });
                }}
                className="rounded-2xl bg-blue-700 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-600"
              >
                Okay, got it
              </button>
            </div>
          </div>
        </div>
      ) */}
    </main>
  );
}

function IncidentCard({ incident, onActivate, onResolve, onArchive, onDelete, onEscalate, isEscalating }: { incident: FoundationIncident; onActivate: () => void; onResolve: () => void; onArchive: () => void; onDelete: () => void; onEscalate: () => void; isEscalating: boolean }) {
  const canEscalate = ["reported", "pending_verification", "active"].includes(incident.status);
  return (
    <article className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-900">{incident.title}</h3>
          <p className="mt-1 text-sm text-slate-600">{incident.location_name} · {pretty(incident.status)}</p>
          <p className="mt-2 text-sm text-slate-600">{incident.route_impact_summary ?? "Route impact under review."}</p>
        </div>
        <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700">{pretty(incident.severity)}</span>
      </div>
      <div className="mt-4 grid gap-2 text-sm md:grid-cols-2">
        <span className="text-slate-600">ID: <span className="font-mono text-xs">{incident.id}</span></span>
        <span className="text-slate-600">Confidence: {Math.round(incident.confidence_score * 100)}%</span>
        <span className="text-slate-600">Force: {incident.latest_prediction?.police_force_required ?? incident.police_force_required ?? "-"}</span>
        <span className="text-slate-600">Barricades: {incident.latest_prediction?.barricades_required ?? incident.barricades_required ?? "-"}</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button type="button" onClick={onActivate} className="rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700">Activate</button>
        <button type="button" onClick={onResolve} className="rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700">Resolve</button>
        <button type="button" onClick={onArchive} className="rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700">Archive</button>
        <button type="button" onClick={onDelete} className="rounded-2xl border border-rose-200 bg-white px-3 py-2 text-sm text-rose-700">Delete</button>
        {canEscalate && (
          <button
            type="button"
            onClick={onEscalate}
            disabled={isEscalating}
            className="rounded-2xl border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-700 transition hover:bg-blue-100 disabled:opacity-60"
          >
            {isEscalating ? "Escalating…" : "⬆ Escalate to Event"}
          </button>
        )}
      </div>
    </article>
  );
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="text-sm text-slate-600">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400" />
    </label>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-bold text-slate-900">{value}</p>
    </div>
  );
}

function MetricCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">{label}</p>
      <h2 className="mt-2 text-2xl font-bold">{value}</h2>
      <p className="mt-3 text-sm leading-6 text-slate-600">{note}</p>
    </article>
  );
}




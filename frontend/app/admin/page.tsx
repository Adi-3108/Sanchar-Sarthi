"use client";

import Link from "next/link";
import { type FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import {
  ApiError,
  createOfficer,
  generateEventFeatures,
  getHealth,
  getMapConfig,
  getModelRuns,
  getSummary,
  loadDemoDataset,
  type CreateOfficerRequest,
  type CreateOfficerResponse,
  type DatasetLoadResponse,
  type FeatureGenerationResponse
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
    return error.body;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Action failed.";
}

function splitScope(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function AdminPage() {
  const queryClient = useQueryClient();
  const { user, ready: authReady } = useFirebaseAuthState();
  const [officerForm, setOfficerForm] = useState<CreateOfficerRequest>({
    email: "officer.demo@sancharsarthi.local",
    firebase_uid: "firebase-officer-demo-001",
    officer_id: "BTP-DEMO-001",
    display_name: "Officer Demo",
    rank: "Traffic Constable",
    police_station: "HSR Layout",
    assigned_corridors: ["ORR East 1"],
    assigned_zones: ["East"]
  });

  const healthQuery = useQuery({
    queryKey: ["admin-health"],
    queryFn: getHealth,
    retry: 1,
    refetchOnWindowFocus: false
  });
  const summaryQuery = useQuery({
    queryKey: ["admin-summary"],
    queryFn: getSummary,
    enabled: authReady && Boolean(user),
    retry: 1,
    refetchOnWindowFocus: false
  });
  const modelRunsQuery = useQuery({
    queryKey: ["admin-model-runs"],
    queryFn: getModelRuns,
    enabled: authReady && Boolean(user),
    retry: 1,
    refetchOnWindowFocus: false
  });
  const mapQuery = useQuery({
    queryKey: ["admin-map-config"],
    queryFn: getMapConfig,
    retry: 1,
    refetchOnWindowFocus: false
  });

  const loadDemoMutation = useMutation<DatasetLoadResponse, unknown>({
    mutationFn: () => loadDemoDataset(),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin-summary"] }),
        queryClient.invalidateQueries({ queryKey: ["admin-model-runs"] })
      ]);
    }
  });
  const generateFeaturesMutation = useMutation<FeatureGenerationResponse, unknown>({
    mutationFn: () => generateEventFeatures(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-summary"] });
    }
  });
  const createOfficerMutation = useMutation<CreateOfficerResponse, unknown, CreateOfficerRequest>({
    mutationFn: (payload) => createOfficer(payload)
  });

  const latestRun = modelRunsQuery.data?.model_runs[0];
  const canRunProtectedActions = authReady && Boolean(user);
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

  if (!authReady || !user) {
    return (
      <main className="min-h-screen bg-bg px-6 py-8 text-copy md:px-10">
        <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-[1fr_380px]">
          <section className="rounded-lg border border-line bg-panel p-8 shadow-panel">
            <p className="text-sm uppercase tracking-[0.24em] text-accent">Sanchar Sarthi</p>
            <h1 className="mt-3 text-4xl font-semibold">{authReady ? "Admin access is protected." : "Checking admin session."}</h1>
            <p className="mt-4 text-muted">Sign in with an admin Firebase account to access seed/reset, role, audit, model, and system controls.</p>
          </section>
          <AuthPanel
            preferredRole="admin"
            title="Admin Firebase sign-in"
            note="Admin mode is not available to public users."
          />
        </div>
      </main>
    );
  }

  function updateOfficerField<Key extends keyof CreateOfficerRequest>(
    key: Key,
    value: CreateOfficerRequest[Key]
  ) {
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

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="rounded-[28px] border border-line/80 bg-panel/90 p-8 shadow-panel">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">Level 1</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
                Sanchar Sarthi admin and control-room operations portal.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
                This surface connects health, dataset analytics, model status, provider status,
                demo dataset actions, feature regeneration, and registered officer creation.
              </p>
            </div>
            <nav className="flex flex-wrap gap-3">
              <Link
                href="/command-center"
                className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy"
              >
                Command center
              </Link>
              <Link
                href="/explorer"
                className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy"
              >
                Explorer
              </Link>
              <Link
                href="/simulation"
                className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy"
              >
                Simulation
              </Link>
              <Link
                href="/settings"
                className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy"
              >
                Settings
              </Link>
            </nav>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.36fr_0.64fr]">
          <AuthPanel
            preferredRole="admin"
            title="Admin Firebase sign-in"
            note="Use a registered Level 1 account for protected analytics, model metadata, dataset operations, and officer management."
          />

          <div className="grid gap-5 md:grid-cols-2">
            <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Backend</p>
              <h2 className="mt-2 text-2xl font-semibold">
                {healthQuery.isLoading ? "Checking" : healthQuery.isError ? "Needs attention" : "Operational"}
              </h2>
              <div className="mt-4 space-y-2 text-sm leading-7 text-muted">
                <p>Database: {healthQuery.data?.database ?? "n/a"}</p>
                <p>Firebase: {healthQuery.data?.auth.firebase ?? "n/a"}</p>
                <p>Priority model: {healthQuery.data?.models.priority ?? "n/a"}</p>
                <p>Resolution model: {healthQuery.data?.models.resolution_time ?? "n/a"}</p>
              </div>
            </article>

            <article className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Map provider</p>
              <h2 className="mt-2 text-2xl font-semibold">{mapQuery.data?.activeProvider ?? "Checking"}</h2>
              <div className="mt-4 space-y-2 text-sm leading-7 text-muted">
                <p>Primary: MapmyIndia / Mappls</p>
                <p>Fallback: {mapQuery.data?.fallbackProvider ?? "osm"}</p>
                <p>Budget: INR {mapQuery.data?.creditsBudgetInr ?? 1000}</p>
                <p>Key available: {mapQuery.data?.mapKeyAvailable ? "yes" : "no"}</p>
              </div>
            </article>

            <article className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel md:col-span-2">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Dataset snapshot</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <Metric label="Total events" value={metric(summaryQuery.data?.total_events)} />
                <Metric label="High priority" value={metric(summaryQuery.data?.high_priority_events)} />
                <Metric label="Road closures" value={metric(summaryQuery.data?.road_closure_required)} />
                <Metric label="Hotspots" value={metric(summaryQuery.data?.hotspot_count)} />
              </div>
            </article>

            <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel md:col-span-2">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Latest model run</p>
              <h2 className="mt-2 text-2xl font-semibold">{latestRun?.model_name ?? "No run metadata yet"}</h2>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <Metric label="Version" value={latestRun?.model_version ?? "n/a"} />
                <Metric label="Training rows" value={metric(latestRun?.training_rows)} />
                <Metric label="Artifact" value={latestRun?.artifact_status ?? "n/a"} />
              </div>
            </article>

            <article className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel md:col-span-2">
              <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Operational controls</p>
                  <h2 className="mt-2 text-2xl font-semibold">Dataset and feature actions</h2>
                </div>
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => loadDemoMutation.mutate()}
                    disabled={!canRunProtectedActions || loadDemoMutation.isPending}
                    className="rounded-2xl border border-accent/50 bg-accent px-4 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {loadDemoMutation.isPending ? "Loading demo dataset" : "Load demo dataset"}
                  </button>
                  <button
                    type="button"
                    onClick={() => generateFeaturesMutation.mutate()}
                    disabled={!canRunProtectedActions || generateFeaturesMutation.isPending}
                    className="rounded-2xl border border-line/80 px-4 py-3 text-sm font-semibold text-copy transition hover:border-accent/60 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {generateFeaturesMutation.isPending ? "Generating features" : "Generate features"}
                  </button>
                </div>
              </div>
              {latestAction ? <p className="mt-4 text-sm leading-7 text-ok">{latestAction}</p> : null}
              {loadDemoMutation.isError ? <p className="mt-3 text-sm text-danger">{errorText(loadDemoMutation.error)}</p> : null}
              {generateFeaturesMutation.isError ? <p className="mt-3 text-sm text-danger">{errorText(generateFeaturesMutation.error)}</p> : null}
              {!canRunProtectedActions ? (
                <p className="mt-3 text-sm leading-7 text-muted">Sign in with a Level 1 Firebase account before running protected admin actions.</p>
              ) : null}
            </article>

            <form onSubmit={handleCreateOfficer} className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel md:col-span-2">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Officer access</p>
              <h2 className="mt-2 text-2xl font-semibold">Create registered police officer</h2>
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <Field label="Officer email" value={officerForm.email} onChange={(value) => updateOfficerField("email", value)} />
                <Field label="Firebase UID" value={officerForm.firebase_uid} onChange={(value) => updateOfficerField("firebase_uid", value)} />
                <Field label="Officer ID" value={officerForm.officer_id} onChange={(value) => updateOfficerField("officer_id", value)} />
                <Field label="Display name" value={officerForm.display_name} onChange={(value) => updateOfficerField("display_name", value)} />
                <Field label="Rank" value={officerForm.rank ?? ""} onChange={(value) => updateOfficerField("rank", value)} />
                <Field label="Police station" value={officerForm.police_station} onChange={(value) => updateOfficerField("police_station", value)} />
                <Field label="Assigned corridors (comma separated)" value={officerForm.assigned_corridors.join(", ")} onChange={(value) => updateOfficerField("assigned_corridors", splitScope(value))} />
                <Field label="Assigned zones (comma separated)" value={officerForm.assigned_zones.join(", ")} onChange={(value) => updateOfficerField("assigned_zones", splitScope(value))} />
              </div>
              <button
                type="submit"
                disabled={!canRunProtectedActions || createOfficerMutation.isPending}
                className="mt-5 rounded-2xl border border-accent/50 bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
              >
                {createOfficerMutation.isPending ? "Creating officer" : "Create officer"}
              </button>
              {createOfficerMutation.isError ? (
                <p className="mt-3 text-sm leading-7 text-danger">{errorText(createOfficerMutation.error)}</p>
              ) : null}
            </form>
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

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line/70 bg-bg/60 p-4">
      <p className="text-[11px] uppercase tracking-[0.22em] text-accentSoft">{label}</p>
      <p className="mt-2 text-xl font-semibold text-copy">{value}</p>
    </div>
  );
}

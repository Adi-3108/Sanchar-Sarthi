"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import {
  getHealth,
  getModelRuns,
  type HealthResponse,
  type ModelArtifactStatus,
  type ModelRunResponse
} from "@/lib/api";

const modelDefinitions = [
  {
    key: "priority_model",
    label: "Priority model",
    statusKey: "priority" as const,
    honestyLabel: "Predicted High or Low urgency from dataset-backed event fields."
  },
  {
    key: "road_closure_model",
    label: "Road-closure likelihood",
    statusKey: "road_closure" as const,
    honestyLabel: "Rule-history score stays primary even when optional ML support exists."
  },
  {
    key: "resolution_time_model",
    label: "Resolution-time estimator",
    statusKey: "resolution_time" as const,
    honestyLabel: "Estimated clearance time, not a guaranteed operational commitment."
  }
];

function statusTone(status: ModelArtifactStatus): string {
  if (status === "loaded") {
    return "border-emerald-400/30 bg-emerald-500/10 text-emerald-200";
  }
  if (status === "dependency_missing") {
    return "border-amber-400/30 bg-amber-500/10 text-amber-100";
  }
  return "border-line bg-bg/60 text-muted";
}

function statusLabel(status: ModelArtifactStatus): string {
  if (status === "loaded") {
    return "Loaded";
  }
  if (status === "dependency_missing") {
    return "Artifact present, dependencies missing";
  }
  return "Artifact not loaded";
}

function formatNumber(value: unknown, digits = 2): string {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "Not available";
  }
  return value.toFixed(digits);
}

function formatTimestamp(value?: string): string {
  if (!value) {
    return "Not available";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Not available";
  }
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(parsed);
}

function latestModelRunByName(modelRuns: ModelRunResponse[] | undefined): Record<string, ModelRunResponse> {
  return Object.fromEntries((modelRuns ?? []).map((row) => [row.model_name, row]));
}

function renderMetrics(modelName: string, modelRun?: ModelRunResponse) {
  const metrics = modelRun?.metrics_json ?? {};

  if (!modelRun) {
    return (
      <p className="text-sm leading-7 text-muted">
        No training metadata has been recorded yet. The backend will continue using dataset-honest rule fallbacks.
      </p>
    );
  }

  if (modelName === "priority_model") {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        <MetricItem label="F1" value={formatNumber(metrics.f1)} />
        <MetricItem label="Recall High" value={formatNumber(metrics.recall_high)} />
        <MetricItem label="Positive rows" value={String(metrics.positive_rows ?? "Not available")} />
        <MetricItem label="Positive rate" value={formatNumber(metrics.positive_rate, 4)} />
      </div>
    );
  }

  if (modelName === "road_closure_model") {
    return (
      <div className="grid gap-3 sm:grid-cols-2">
        <MetricItem label="PR-AUC" value={formatNumber(metrics.pr_auc, 4)} />
        <MetricItem label="Recall TRUE" value={formatNumber(metrics.recall_true, 4)} />
        <MetricItem label="Positive rows" value={String(metrics.positive_rows ?? "Not available")} />
        <MetricItem label="Positive rate" value={formatNumber(metrics.positive_rate, 4)} />
      </div>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <MetricItem label="MAE minutes" value={formatNumber(metrics.mae_minutes)} />
      <MetricItem label="R2 score" value={formatNumber(metrics.r2_score, 4)} />
      <MetricItem label="Qualifying rows" value={String(metrics.qualifying_rows ?? "Not available")} />
      <MetricItem label="Data filter" value={String(metrics.data_filter ?? "Not available")} />
    </div>
  );
}

function MetricItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line/70 bg-bg/60 p-4">
      <p className="text-[11px] uppercase tracking-[0.22em] text-accentSoft">{label}</p>
      <p className="mt-2 text-sm leading-6 text-copy">{value}</p>
    </div>
  );
}

export default function ModelInsightsPage() {
  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: 1,
    refetchOnWindowFocus: false
  });
  const modelRunsQuery = useQuery({
    queryKey: ["model-runs"],
    queryFn: getModelRuns,
    retry: 1,
    refetchOnWindowFocus: false
  });

  const health = healthQuery.data;
  const modelRuns = modelRunsQuery.data?.model_runs ?? [];
  const modelRunMap = latestModelRunByName(modelRuns);
  const latestRecordedRun = [...modelRuns].sort((a, b) => b.created_at.localeCompare(a.created_at))[0];

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">
        <section className="overflow-hidden rounded-[28px] border border-line/80 bg-panel/90 p-8 shadow-panel">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">Model insights</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
                Dataset-honest prediction diagnostics for Phase 7.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted md:text-lg">
                This view tracks which prediction artifacts exist, what the latest recorded training run says,
                and when EventFlow AI is still operating on explainable rule fallbacks.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:items-end">
              <Link
                href="/command-center"
                className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy"
              >
                Back to command center
              </Link>
              <div className="rounded-3xl border border-accent/30 bg-accent/10 px-5 py-4">
                <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Latest recorded run</p>
                <p className="mt-2 text-2xl font-semibold text-copy">
                  {latestRecordedRun ? formatTimestamp(latestRecordedRun.created_at) : "No runs yet"}
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
          <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel">
            <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">System health</p>
            <h2 className="mt-2 text-2xl font-semibold">Backend and artifact state</h2>
            <div className="mt-5 space-y-3 rounded-3xl border border-line/70 bg-bg/60 p-5 font-mono text-sm leading-7 text-copy">
              {healthQuery.isLoading && <p>Checking backend heartbeat...</p>}
              {healthQuery.isError && (
                <p className="text-danger">
                  {healthQuery.error instanceof Error ? healthQuery.error.message : "Backend unavailable."}
                </p>
              )}
              {health && (
                <>
                  <p>Status: {health.status}</p>
                  <p>Database: {health.database}</p>
                  <p>Priority artifact: {statusLabel(health.models.priority)}</p>
                  <p>Road-closure artifact: {statusLabel(health.models.road_closure)}</p>
                  <p>Resolution-time artifact: {statusLabel(health.models.resolution_time)}</p>
                  <p>Firebase: {health.auth.firebase}</p>
                </>
              )}
            </div>
          </article>

          <article className="rounded-[24px] border border-line/70 bg-panel/85 p-6 shadow-panel">
            <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Interpretation guide</p>
            <h2 className="mt-2 text-2xl font-semibold">How to read this page</h2>
            <ul className="mt-5 space-y-3 text-sm leading-7 text-muted">
              <li>`Artifact not loaded` means no saved model file exists yet, so rules remain active.</li>
              <li>`Artifact present, dependencies missing` means a model file exists but local ML packages are not installed.</li>
              <li>Road-closure likelihood stays rule-history first even when optional ML support is available.</li>
              <li>Resolution-time metrics only use rows that pass the reliable timestamp filter from Phase 7.</li>
            </ul>
          </article>
        </section>

        <section className="grid gap-5">
          {modelDefinitions.map((definition) => {
            const healthStatus: ModelArtifactStatus =
              health?.models[definition.statusKey] ?? "not_loaded";
            const modelRun = modelRunMap[definition.key];
            const metricsStatus =
              typeof modelRun?.metrics_json.status === "string" ? modelRun.metrics_json.status : "not_recorded";

            return (
              <article
                key={definition.key}
                className="rounded-[24px] border border-line/70 bg-panel/85 p-6 shadow-panel"
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="max-w-2xl">
                    <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">{definition.label}</p>
                    <h2 className="mt-2 text-2xl font-semibold">{definition.label}</h2>
                    <p className="mt-3 text-sm leading-7 text-muted">{definition.honestyLabel}</p>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <span className={`rounded-full border px-3 py-1 text-xs uppercase tracking-[0.18em] ${statusTone(healthStatus)}`}>
                      {statusLabel(healthStatus)}
                    </span>
                    <span className="rounded-full border border-line px-3 py-1 text-xs uppercase tracking-[0.18em] text-muted">
                      Metrics: {metricsStatus.replaceAll("_", " ")}
                    </span>
                  </div>
                </div>

                <div className="mt-6 grid gap-5 lg:grid-cols-[0.75fr_1.25fr]">
                  <div className="rounded-3xl border border-line/70 bg-bg/60 p-5 text-sm leading-7 text-copy">
                    <p>Model version: {modelRun?.model_version ?? "Not recorded"}</p>
                    <p>Training rows: {modelRun?.training_rows ?? "Not recorded"}</p>
                    <p>Test rows: {modelRun?.test_rows ?? "Not recorded"}</p>
                    <p>Artifact available: {modelRun ? (modelRun.artifact_available ? "Yes" : "No") : "Not recorded"}</p>
                    <p>Recorded at: {formatTimestamp(modelRun?.created_at)}</p>
                  </div>
                  <div>{modelRunsQuery.isLoading ? <p className="text-sm text-muted">Loading model metrics...</p> : renderMetrics(definition.key, modelRun)}</div>
                </div>
              </article>
            );
          })}
        </section>

        {modelRunsQuery.isError ? (
          <section className="rounded-[24px] border border-danger/30 bg-danger/10 p-5 text-sm text-danger shadow-panel">
            {modelRunsQuery.error instanceof Error
              ? modelRunsQuery.error.message
              : "Model insights endpoint is unavailable right now."}
          </section>
        ) : null}
      </div>
    </main>
  );
}

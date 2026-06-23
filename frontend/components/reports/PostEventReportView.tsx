"use client";

import type { PostEventReportResponse } from "@/lib/api";

export type PostEventReportViewProps = {
  report: PostEventReportResponse | null | undefined;
  className?: string;
};

function formatNumber(value?: number | null, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return value.toFixed(digits);
}

function reportMetric(report: PostEventReportResponse, key: string): string {
  const value = report.report_json[key];
  if (typeof value === "number") {
    return String(value);
  }
  if (typeof value === "string") {
    return value
      .replace(/[_]/g, " ")
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ");
  }
  return "n/a";
}

export function PostEventReportView({ report, className }: PostEventReportViewProps) {
  if (!report) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-line/70 bg-panel/85 p-6 text-sm text-muted ${
          className ?? ""
        }`}
      >
        Generate a post-event report to see after-action lessons and future playbook guidance.
      </section>
    );
  }

  return (
    <section
      className={`rounded-[28px] border border-line/70 bg-panel/85 p-6 shadow-panel ${
        className ?? ""
      }`}
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-accentSoft">Post-event learning</p>
          <h2 className="mt-2 text-2xl font-semibold text-copy">After-action report</h2>
          <p className="mt-3 text-sm leading-7 text-muted">{report.event_summary}</p>
        </div>
        <div className="rounded-full border border-accent/30 bg-accent/10 px-4 py-2 text-xs font-bold uppercase tracking-[0.18em] text-accent">
          {report.final_status ?? "review generated"}
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-4">
        <MetricCard label="Predicted impact" value={formatNumber(report.predicted_impact_score)} />
        <MetricCard label="Observed impact" value={formatNumber(report.simulated_actual_impact_score)} />
        <MetricCard label="Deviation" value={formatNumber(report.impact_deviation)} />
        <MetricCard label="Reports considered" value={reportMetric(report, "report_count")} />
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <NarrativeCard title="Prediction summary" body={report.prediction_summary} />
        <NarrativeCard title="Recommendation summary" body={report.recommendation_summary} />
        <NarrativeCard title="Citizen report summary" body={report.citizen_report_summary ?? "No report summary was available."} />
        <NarrativeCard title="Live escalation summary" body={report.live_escalation_summary ?? "No live escalation summary was available."} />
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <NarrativeCard title="Lessons learned" body={report.lessons_learned} tone="accent" />
        <NarrativeCard title="Future recommendations" body={report.future_recommendations} tone="accent" />
      </div>

      <div className="mt-6 rounded-3xl border border-line/70 bg-panelAlt/90 p-4">
        <div className="flex items-center justify-between gap-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-muted">Structured learning snapshot</p>
          <p className="text-xs text-muted">Stored in `post_event_reports.report_json`</p>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="High-confidence reports" value={reportMetric(report, "high_confidence_report_count")} />
          <MetricCard label="Live updates" value={reportMetric(report, "live_update_count")} />
          <MetricCard label="Critical updates" value={reportMetric(report, "critical_live_update_count")} />
          <MetricCard label="Weather source" value={reportMetric(report, "recommendation_weather_source")} />
        </div>
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-2xl border border-line/70 bg-bg/80 p-4">
      <p className="text-[11px] uppercase tracking-[0.18em] text-muted">{label}</p>
      <p className="mt-2 text-lg font-semibold text-copy">{value}</p>
    </article>
  );
}

function NarrativeCard({
  title,
  body,
  tone = "slate"
}: {
  title: string;
  body: string;
  tone?: "slate" | "accent";
}) {
  const toneClass =
    tone === "accent"
      ? "border-accent/30 bg-accent/10"
      : "border-line/70 bg-bg/80";

  return (
    <article className={`rounded-3xl border p-4 ${toneClass}`}>
      <p className="text-[11px] uppercase tracking-[0.2em] text-accentSoft">{title}</p>
      <p className="mt-3 text-sm leading-7 text-copy">{body}</p>
    </article>
  );
}

export default PostEventReportView;

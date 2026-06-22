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
    return value;
  }
  return "n/a";
}

export function PostEventReportView({ report, className }: PostEventReportViewProps) {
  if (!report) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-200 bg-white p-6 text-sm text-slate-500 ${
          className ?? ""
        }`}
      >
        Generate a post-event report to see after-action lessons and future playbook guidance.
      </section>
    );
  }

  return (
    <section
      className={`rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm ${
        className ?? ""
      }`}
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-emerald-300/80">Post-event learning</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">After-action report</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">{report.event_summary}</p>
        </div>
        <div className="rounded-full border border-emerald-200 bg-emerald-400/10 px-4 py-2 text-xs uppercase tracking-[0.18em] text-emerald-100">
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
        <NarrativeCard title="Lessons learned" body={report.lessons_learned} tone="emerald" />
        <NarrativeCard title="Future recommendations" body={report.future_recommendations} tone="cyan" />
      </div>

      <div className="mt-6 rounded-3xl border border-slate-200 bg-white p-4">
        <div className="flex items-center justify-between gap-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Structured learning snapshot</p>
          <p className="text-xs text-slate-500">Stored in `post_event_reports.report_json`</p>
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
    <article className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-900">{value}</p>
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
  tone?: "slate" | "emerald" | "cyan";
}) {
  const toneClass =
    tone === "emerald"
      ? "border-emerald-400/20 bg-emerald-400/10"
      : tone === "cyan"
        ? "border-cyan-400/20 bg-cyan-400/10"
        : "border-slate-200 bg-white";

  return (
    <article className={`rounded-3xl border p-4 ${toneClass}`}>
      <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">{title}</p>
      <p className="mt-3 text-sm leading-7 text-slate-700">{body}</p>
    </article>
  );
}

export default PostEventReportView;

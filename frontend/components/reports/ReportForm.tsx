"use client";

import { type FormEvent, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import {
  ApiError,
  submitCongestionReport,
  type CitizenReportCreateRequest,
  type CitizenReportResponse,
  type CitizenReportSource
} from "@/lib/api";
import { type AppLanguage, t } from "@/lib/i18n";
import { useCommandStore } from "@/lib/stores/useCommandStore";

const reportTypes = [
  { value: "road_blockage", label: "Road blockage" },
  { value: "congestion", label: "Heavy congestion" },
  { value: "accident", label: "Accident" },
  { value: "illegal_parking", label: "Illegal parking" },
  { value: "waterlogging", label: "Waterlogging" }
];

const severities = ["Low", "Medium", "High", "Critical"];
const reportSources: Array<{ value: CitizenReportSource; label: string }> = [
  { value: "citizen", label: "Citizen" },
  { value: "field_officer", label: "Field officer" },
  { value: "control_room", label: "Control room" }
];

function confidencePercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

function errorText(error: unknown): string {
  if (error instanceof ApiError) {
    return error.body;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Report submission failed.";
}

const descriptionLanguageOptions = [
  { value: "auto", label: "Auto-detect" },
  { value: "en", label: "English" },
  { value: "kn", label: "Kannada" },
  { value: "hi", label: "Hindi" },
  { value: "other", label: "Other" }
];

export function ReportForm() {
  const { language } = useCommandStore();
  const [reportSource, setReportSource] = useState<CitizenReportSource>("citizen");
  const [reportType, setReportType] = useState("road_blockage");
  const [severity, setSeverity] = useState("High");
  const [latitude, setLatitude] = useState("12.9716");
  const [longitude, setLongitude] = useState("77.5946");
  const [description, setDescription] = useState("");
  const [reportLanguage, setReportLanguage] = useState("auto");
  const [locationMessage, setLocationMessage] = useState<string | null>(null);

  const labels = useMemo(() => reportLabelsFor(language), [language]);
  const mutation = useMutation<CitizenReportResponse, unknown, CitizenReportCreateRequest>({
    mutationFn: (payload) => submitCongestionReport(payload)
  });

  function useBrowserLocation() {
    if (!navigator.geolocation) {
      setLocationMessage("Location is not available in this browser.");
      return;
    }

    setLocationMessage("Fetching location...");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude.toFixed(6));
        setLongitude(position.coords.longitude.toFixed(6));
        setLocationMessage("Location added.");
      },
      () => setLocationMessage("Location permission was not granted."),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const lat = Number(latitude);
    const lng = Number(longitude);

    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      setLocationMessage("Enter valid Bengaluru coordinates.");
      return;
    }

    mutation.mutate({
      report_source: reportSource,
      report_type: reportType,
      latitude: lat,
      longitude: lng,
      severity,
      description,
      language: reportLanguage
    });
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
      <form
        onSubmit={handleSubmit}
        className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div className="flex flex-col gap-4 border-b border-slate-200 pb-5 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-blue-600">Sanchar Sarthi</p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-900">{labels.reportIssue}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">{labels.publicNote}</p>
          </div>
          <label className="min-w-40 text-sm text-slate-600">
            <span className="mb-2 block text-[11px] uppercase tracking-[0.18em] text-slate-500">
              {labels.language}
            </span>
            <select
              value={reportLanguage}
              onChange={(event) => setReportLanguage(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-slate-900 outline-none transition focus:border-blue-400"
            >
              {descriptionLanguageOptions.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-6 grid gap-5 md:grid-cols-2">
          <label className="text-sm text-slate-600">
            <span className="mb-2 block text-[11px] uppercase tracking-[0.18em] text-slate-500">
              Source
            </span>
            <select
              value={reportSource}
              onChange={(event) => setReportSource(event.target.value as CitizenReportSource)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-3 text-slate-900 outline-none transition focus:border-blue-400"
            >
              {reportSources.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm text-slate-600">
            <span className="mb-2 block text-[11px] uppercase tracking-[0.18em] text-slate-500">
              {labels.issueType}
            </span>
            <select
              value={reportType}
              onChange={(event) => setReportType(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-3 text-slate-900 outline-none transition focus:border-blue-400"
            >
              {reportTypes.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm text-slate-600">
            <span className="mb-2 block text-[11px] uppercase tracking-[0.18em] text-slate-500">
              {labels.severity}
            </span>
            <select
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-3 text-slate-900 outline-none transition focus:border-blue-400"
            >
              {severities.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
            <label className="text-sm text-slate-600">
              <span className="mb-2 block text-[11px] uppercase tracking-[0.18em] text-slate-500">
                {labels.latitude}
              </span>
              <input
                value={latitude}
                onChange={(event) => setLatitude(event.target.value)}
                inputMode="decimal"
                className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-3 text-slate-900 outline-none transition focus:border-blue-400"
              />
            </label>
            <label className="text-sm text-slate-600">
              <span className="mb-2 block text-[11px] uppercase tracking-[0.18em] text-slate-500">
                {labels.longitude}
              </span>
              <input
                value={longitude}
                onChange={(event) => setLongitude(event.target.value)}
                inputMode="decimal"
                className="w-full rounded-2xl border border-slate-200 bg-white px-3 py-3 text-slate-900 outline-none transition focus:border-blue-400"
              />
            </label>
            <button
              type="button"
              onClick={useBrowserLocation}
              className="self-end rounded-2xl border border-blue-600 bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:border-blue-500 hover:bg-blue-600"
            >
              {labels.useLocation}
            </button>
          </div>
        </div>

        {locationMessage ? <p className="mt-3 text-sm text-slate-500">{locationMessage}</p> : null}

        <label className="mt-6 block text-sm text-slate-600">
          <span className="mb-2 block text-[11px] uppercase tracking-[0.18em] text-slate-500">
            {labels.description}
          </span>
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            minLength={10}
            maxLength={500}
            required
            rows={6}
            className="w-full resize-none rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-600 focus:border-blue-400"
            placeholder="Road blocked near junction..."
          />
        </label>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="rounded-2xl border border-blue-600 bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {mutation.isPending ? labels.submitting : labels.submit}
          </button>
          {mutation.isError ? (
            <p className="text-sm leading-6 text-rose-600">{errorText(mutation.error)}</p>
          ) : null}
        </div>
      </form>

      <ReportResultPanel labels={labels} result={mutation.data} />
    </div>
  );
}

function ReportResultPanel({
  labels,
  result
}: {
  labels: Record<string, string>;
  result: CitizenReportResponse | undefined;
}) {
  if (!result) {
    return (
      <aside className="rounded-[28px] border border-slate-200 bg-white p-6 text-sm leading-7 text-slate-500">
        {labels.publicNote}
      </aside>
    );
  }

  return (
    <aside className="rounded-[28px] border border-emerald-200 bg-emerald-50 p-6 shadow-sm">
      <p className="text-[11px] uppercase tracking-[0.24em] text-emerald-700">{labels.accepted}</p>
      <h2 className="mt-3 text-2xl font-semibold text-slate-900">{result.new_alert_level}</h2>
      <div className="mt-6 grid gap-3">
        <Metric label={labels.confidence} value={confidencePercent(result.report_confidence)} />
        <Metric label={labels.alertLevel} value={result.new_alert_level} />
        <Metric label={labels.matchedEvent} value={result.matched_event_id ?? labels.notMatched} />
        <Metric label="Impact delta" value={`+${result.impact_score_change.toFixed(1)}`} />
      </div>
      {result.translated_description ? (
        <p className="mt-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm leading-7 text-slate-600">
          {result.translated_description}
        </p>
      ) : null}
      <p className="mt-5 text-sm leading-7 text-slate-700">{result.recommended_action}</p>
    </aside>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function reportLabelsFor(language: AppLanguage | "hi"): Record<string, string> {
  const keys = [
    "reportIssue",
    "issueType",
    "severity",
    "description",
    "language",
    "latitude",
    "longitude",
    "useLocation",
    "submit",
    "submitting",
    "accepted",
    "confidence",
    "alertLevel",
    "recommendedAction",
    "matchedEvent",
    "notMatched",
    "publicNote"
  ];

  const resolvedLanguage: AppLanguage = language === "hi" ? "en" : language;
  return Object.fromEntries(keys.map((key) => [key, t(resolvedLanguage, key)]));
}

export default ReportForm;


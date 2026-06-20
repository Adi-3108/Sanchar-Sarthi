"use client";

import type { WeatherAdjustmentResponse } from "@/lib/api";

export type WeatherRiskPanelProps = {
  weatherRisk: WeatherAdjustmentResponse | null | undefined;
  className?: string;
};

function formatCondition(value: string): string {
  return value.replaceAll("_", " ");
}

export function WeatherRiskPanel({ weatherRisk, className }: WeatherRiskPanelProps) {
  if (!weatherRisk) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-700/80 bg-slate-950/60 p-6 text-sm text-slate-400 ${
          className ?? ""
        }`}
      >
        Weather risk guidance is not available yet.
      </section>
    );
  }

  return (
    <section
      className={`flex flex-col h-full rounded-[28px] border border-slate-800/80 bg-slate-950/85 p-6 shadow-[0_18px_40px_rgba(2,6,23,0.35)] ${
        className ?? ""
      }`}
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-cyan-300/80">Weather Risk</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-100">Rain, visibility, and waterlogging posture</h2>
        </div>
        <p className="text-3xl font-semibold text-slate-100">{weatherRisk.weather_factor.toFixed(2)}x</p>
      </div>

      <div className="mt-6 grid gap-4 grid-cols-2">
        <MetricCard label="Condition" value={formatCondition(weatherRisk.weather_condition)} />
        <MetricCard label="Rain mm" value={weatherRisk.rain_mm.toFixed(1)} />
        <MetricCard
          label="Visibility"
          value={weatherRisk.visibility_m != null ? `${weatherRisk.visibility_m.toFixed(0)} m` : "Not provided"}
        />
        <MetricCard label="Waterlogging" value={formatCondition(weatherRisk.waterlogging_risk)} />
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        {weatherRisk.reason_codes.length ? (
          weatherRisk.reason_codes.map((reason) => (
            <span
              key={reason}
              className="rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-300"
            >
              {formatCondition(reason)}
            </span>
          ))
        ) : (
          <span className="rounded-full border border-slate-800/80 bg-slate-950/70 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-500">
            Neutral weather modifier
          </span>
        )}
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-4">
          <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Source</p>
          <p className="mt-2 text-sm leading-6 text-slate-200">
            {formatCondition(weatherRisk.source)}
            {weatherRisk.provider ? ` via ${formatCondition(weatherRisk.provider)}` : ""}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-4">
          <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Low visibility</p>
          <p className="mt-2 text-sm leading-6 text-slate-200">{weatherRisk.low_visibility ? "Yes" : "No"}</p>
        </article>
      </div>

      <p className="mt-auto pt-5 text-sm leading-7 text-slate-300">{weatherRisk.note}</p>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-4">
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-100">{value}</p>
    </article>
  );
}

export default WeatherRiskPanel;

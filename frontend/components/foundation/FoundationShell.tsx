"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import AuthPanel from "@/components/auth/AuthPanel";
import {
  ApiError,
  getFoundationControlRoom,
  getFoundationIncidents,
  seedFoundationData,
  voteFoundationIncident,
  type FoundationBrowseResponse,
  type FoundationIncident
} from "@/lib/api";
import { useFirebaseAuthState } from "@/lib/auth";
import { type AppLanguage, languageOptions } from "@/lib/i18n";

type Mode = "user" | "control" | "admin";

const copy = {
  en: {
    app: "Sanchar Sarthi",
    dept: "Bengaluru Traffic Incident Response",
    user: "User mode",
    control: "Control room",
    admin: "Admin",
    active: "Active incidents",
    reports: "User reported incidents",
    map: "Bengaluru map and hotspots",
    stations: "Station mapping",
    route: "Alternate routes",
    voteTrue: "Vote true",
    voteFalse: "Vote false",
    report: "Report incident",
    login: "Login required for voting and reporting.",
    protected: "Protected operational access",
    seed: "Seed foundation data",
    prediction: "Prediction",
    force: "Force",
    barricades: "Barricades",
    confidence: "Confidence",
    status: "Status",
    station: "Station",
    impact: "Route impact"
  },
  hi: {
    app: "Sanchar Sarthi",
    dept: "बेंगलुरु यातायात घटना प्रतिक्रिया",
    user: "उपयोगकर्ता मोड",
    control: "कंट्रोल रूम",
    admin: "एडमिन",
    active: "सक्रिय घटनाएं",
    reports: "उपयोगकर्ता रिपोर्ट",
    map: "बेंगलुरु मानचित्र और हॉटस्पॉट",
    stations: "थाना मैपिंग",
    route: "वैकल्पिक मार्ग",
    voteTrue: "सही वोट",
    voteFalse: "गलत वोट",
    report: "घटना रिपोर्ट करें",
    login: "वोट और रिपोर्ट के लिए लॉगिन आवश्यक है।",
    protected: "सुरक्षित परिचालन पहुंच",
    seed: "फाउंडेशन डेटा सीड करें",
    prediction: "पूर्वानुमान",
    force: "बल",
    barricades: "बैरिकेड",
    confidence: "विश्वास",
    status: "स्थिति",
    station: "थाना",
    impact: "मार्ग प्रभाव"
  },
  kn: {
    app: "Sanchar Sarthi",
    dept: "ಬೆಂಗಳೂರು ಸಂಚಾರ ಘಟನೆ ಪ್ರತಿಕ್ರಿಯೆ",
    user: "ಬಳಕೆದಾರ ಮೋಡ್",
    control: "ನಿಯಂತ್ರಣ ಕೊಠಡಿ",
    admin: "ನಿರ್ವಾಹಕ",
    active: "ಸಕ್ರಿಯ ಘಟನೆಗಳು",
    reports: "ಬಳಕೆದಾರ ವರದಿಗಳು",
    map: "ಬೆಂಗಳೂರು ನಕ್ಷೆ ಮತ್ತು ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು",
    stations: "ಠಾಣೆ ಮ್ಯಾಪಿಂಗ್",
    route: "ಪರ್ಯಾಯ ಮಾರ್ಗಗಳು",
    voteTrue: "ಸರಿ ಮತ",
    voteFalse: "ತಪ್ಪು ಮತ",
    report: "ಘಟನೆ ವರದಿ ಮಾಡಿ",
    login: "ಮತದಾನ ಮತ್ತು ವರದಿಗೆ ಲಾಗಿನ್ ಅಗತ್ಯ.",
    protected: "ಸುರಕ್ಷಿತ ಕಾರ್ಯಾಚರಣೆ ಪ್ರವೇಶ",
    seed: "ಮೂಲ ಡೇಟಾ ಸೀಡ್ ಮಾಡಿ",
    prediction: "ಮುನ್ಸೂಚನೆ",
    force: "ಪಡೆ",
    barricades: "ಬ್ಯಾರಿಕೇಡ್",
    confidence: "ವಿಶ್ವಾಸ",
    status: "ಸ್ಥಿತಿ",
    station: "ಠಾಣೆ",
    impact: "ಮಾರ್ಗ ಪರಿಣಾಮ"
  }
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

export function FoundationShell({ mode }: { mode: Mode }) {
  const queryClient = useQueryClient();
  const { user, ready } = useFirebaseAuthState();
  const [language, setLanguage] = useState<AppLanguage>("en");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const labels = copy[language];
  const protectedMode = mode !== "user";

  const query = useQuery({
    queryKey: [mode === "control" ? "foundation-control" : "foundation-public"],
    queryFn: mode === "control" ? getFoundationControlRoom : getFoundationIncidents,
    enabled: !protectedMode || (ready && Boolean(user)),
    retry: 1,
    refetchOnWindowFocus: false
  });

  const seedMutation = useMutation({
    mutationFn: () => seedFoundationData(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["foundation-public"] });
      await queryClient.invalidateQueries({ queryKey: ["foundation-control"] });
    }
  });

  const voteMutation = useMutation({
    mutationFn: ({ incidentId, voteValue }: { incidentId: string; voteValue: "true" | "false" }) =>
      voteFoundationIncident(incidentId, voteValue),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["foundation-public"] });
    }
  });

  const data = query.data;
  const incidents = data?.incidents ?? [];
  const activeIncidents = incidents.filter((incident) => ["active", "escalated", "resolved"].includes(incident.status));
  const reportedIncidents = incidents.filter((incident) => ["reported", "pending_verification", "rejected"].includes(incident.status));
  const heading = mode === "admin" ? labels.admin : mode === "control" ? labels.control : labels.user;

  if (protectedMode && ready && !user) {
    return (
      <main className="min-h-screen bg-bg p-6 text-copy">
        <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-[1fr_380px]">
          <Header language={language} setLanguage={setLanguage} sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
          <AuthPanel
            preferredRole={mode === "admin" ? "admin" : "control_room"}
            title={labels.protected}
            note={labels.login}
          />
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-bg text-copy">
      <Header language={language} setLanguage={setLanguage} sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      <div className="mx-auto grid max-w-7xl gap-5 px-4 py-5 lg:grid-cols-[260px_1fr]">
        {sidebarOpen ? (
          <aside className="rounded-lg border border-line bg-panel p-4 shadow-panel">
            <nav className="grid gap-2 text-sm font-semibold">
              <Link className="rounded-md px-3 py-2 hover:bg-panelAlt" href="/user">{labels.user}</Link>
              <Link className="rounded-md px-3 py-2 hover:bg-panelAlt" href="/control-room">{labels.control}</Link>
              <Link className="rounded-md px-3 py-2 hover:bg-panelAlt" href="/admin">{labels.admin}</Link>
              <Link className="rounded-md px-3 py-2 hover:bg-panelAlt" href="/reports">{labels.report}</Link>
            </nav>
            <div className="mt-5 rounded-md border border-line bg-panelAlt p-3 text-sm text-muted">
              {labels.login}
            </div>
            {mode === "user" && !user ? (
              <div className="mt-5">
                <AuthPanel
                  preferredRole="citizen"
                  title="Citizen login"
                  note="Sign in to vote and use authenticated reporting workflows."
                />
              </div>
            ) : null}
          </aside>
        ) : null}

        <section className="grid gap-5">
          <div className="rounded-lg border border-line bg-panel p-5 shadow-panel">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">{labels.dept}</p>
            <div className="mt-2 flex flex-wrap items-end justify-between gap-3">
              <h1 className="text-3xl font-bold">{heading}</h1>
              {mode === "admin" ? (
                <button
                  className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                  disabled={seedMutation.isPending}
                  onClick={() => seedMutation.mutate()}
                  type="button"
                >
                  {seedMutation.isPending ? "Seeding" : labels.seed}
                </button>
              ) : null}
            </div>
            {seedMutation.data ? (
              <p className="mt-3 text-sm text-ok">Seed complete: {seedMutation.data.incidents} incidents created.</p>
            ) : null}
            {query.isError ? <p className="mt-3 text-sm text-danger">{errorText(query.error)}</p> : null}
          </div>

          <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
            <IncidentSection
              title={labels.active}
              incidents={activeIncidents}
              labels={labels}
              canVote={Boolean(user)}
              onVote={(incidentId, voteValue) => voteMutation.mutate({ incidentId, voteValue })}
            />
            <IncidentSection
              title={labels.reports}
              incidents={reportedIncidents}
              labels={labels}
              canVote={Boolean(user)}
              compact
              onVote={(incidentId, voteValue) => voteMutation.mutate({ incidentId, voteValue })}
            />
          </div>

          <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
            <MapPanel data={data} labels={labels} />
            <StationPanel data={data} labels={labels} />
          </div>
        </section>
      </div>
    </main>
  );
}

function Header({
  language,
  setLanguage,
  sidebarOpen,
  setSidebarOpen
}: {
  language: AppLanguage;
  setLanguage: (language: AppLanguage) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (value: boolean) => void;
}) {
  const labels = copy[language];
  return (
    <header className="border-b border-line bg-panel">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-3">
          <button className="rounded-md border border-line px-3 py-2 text-sm" onClick={() => setSidebarOpen(!sidebarOpen)} type="button">
            ☰
          </button>
          <div>
            <p className="text-xl font-bold text-accent">{labels.app}</p>
            <p className="text-xs text-muted">{labels.dept}</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Link className="rounded-md border border-line px-3 py-2 text-sm" href="/user">{labels.user}</Link>
          <Link className="rounded-md border border-line px-3 py-2 text-sm" href="/control-room">{labels.control}</Link>
          <Link className="rounded-md border border-line px-3 py-2 text-sm" href="/admin">{labels.admin}</Link>
          <select
            className="rounded-md border border-line bg-panel px-3 py-2 text-sm"
            value={language}
            onChange={(event) => setLanguage(event.target.value as AppLanguage)}
          >
            {languageOptions.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
      </div>
    </header>
  );
}

function IncidentSection({
  title,
  incidents,
  labels,
  canVote,
  compact = false,
  onVote
}: {
  title: string;
  incidents: FoundationIncident[];
  labels: (typeof copy)["en"];
  canVote: boolean;
  compact?: boolean;
  onVote: (incidentId: string, voteValue: "true" | "false") => void;
}) {
  return (
    <section className="rounded-lg border border-line bg-panel p-4 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-bold">{title}</h2>
        <Link href="/reports" className="rounded-md bg-accent px-3 py-2 text-sm font-semibold text-white">{labels.report}</Link>
      </div>
      <div className="mt-4 grid gap-3">
        {incidents.map((incident) => (
          <article key={incident.id} className="rounded-lg border border-line bg-white p-4">
            <div className="flex flex-wrap justify-between gap-2">
              <div>
                <h3 className="font-bold">{incident.title}</h3>
                <p className="text-sm text-muted">{incident.location_name}</p>
              </div>
              <span className="rounded-full border border-line bg-panelAlt px-3 py-1 text-xs font-semibold uppercase">{incident.severity}</span>
            </div>
            {!compact ? <p className="mt-3 text-sm leading-6 text-muted">{incident.description}</p> : null}
            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              <Info label={labels.status} value={incident.status} />
              <Info label={labels.station} value={incident.assigned_station_name ?? "Pending"} />
              <Info label={labels.confidence} value={`${Math.round(incident.confidence_score * 100)}%`} />
              <Info label={labels.impact} value={incident.route_impact_summary ?? "Under review"} />
            </dl>
            <div className="mt-3 flex flex-wrap gap-2">
              <button className="rounded-md border border-line px-3 py-2 text-sm disabled:opacity-50" disabled={!canVote} onClick={() => onVote(incident.id, "true")} type="button">
                {labels.voteTrue} ({incident.true_vote_count})
              </button>
              <button className="rounded-md border border-line px-3 py-2 text-sm disabled:opacity-50" disabled={!canVote} onClick={() => onVote(incident.id, "false")} type="button">
                {labels.voteFalse} ({incident.false_vote_count})
              </button>
              <button className="rounded-md border border-accent px-3 py-2 text-sm font-semibold text-accent" type="button">
                {labels.route}
              </button>
            </div>
            {incident.latest_prediction ? (
              <p className="mt-3 text-xs text-muted">
                {labels.prediction}: {incident.latest_prediction.predicted_severity} · {labels.force}: {incident.latest_prediction.police_force_required} · {labels.barricades}: {incident.latest_prediction.barricades_required}
              </p>
            ) : null}
          </article>
        ))}
        {!incidents.length ? <p className="text-sm text-muted">No incidents in this group.</p> : null}
      </div>
    </section>
  );
}

function MapPanel({ data, labels }: { data?: FoundationBrowseResponse; labels: (typeof copy)["en"] }) {
  const points = useMemo(() => data?.incidents.slice(0, 8) ?? [], [data]);
  return (
    <section className="rounded-lg border border-line bg-panel p-4 shadow-panel">
      <h2 className="text-xl font-bold">{labels.map}</h2>
      <div className="mt-4 min-h-[280px] rounded-lg border border-line bg-[linear-gradient(135deg,#dcecff,#f8fbff)] p-4">
        <div className="grid h-full min-h-[240px] grid-cols-2 gap-3 md:grid-cols-4">
          {points.map((incident) => (
            <div key={incident.id} className="self-center rounded-lg border border-accent bg-white p-3 text-xs shadow-panel">
              <p className="font-bold">{incident.location_name}</p>
              <p className="text-muted">{incident.status}</p>
              <p className="text-muted">{incident.latitude.toFixed(3)}, {incident.longitude.toFixed(3)}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function StationPanel({ data, labels }: { data?: FoundationBrowseResponse; labels: (typeof copy)["en"] }) {
  return (
    <section className="rounded-lg border border-line bg-panel p-4 shadow-panel">
      <h2 className="text-xl font-bold">{labels.stations}</h2>
      <div className="mt-4 grid gap-3">
        {(data?.stations ?? []).map((station) => (
          <div key={station.station_code} className="rounded-lg border border-line bg-white p-3 text-sm">
            <p className="font-bold">{station.name}</p>
            <p className="text-muted">{station.locality} · {station.station_code}</p>
            <p className="text-muted">{station.contact_number ?? "Contact pending"}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-[0.16em] text-muted">{label}</dt>
      <dd className="font-semibold">{value}</dd>
    </div>
  );
}

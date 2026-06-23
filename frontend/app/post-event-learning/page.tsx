"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import PostEventReportView from "@/components/reports/PostEventReportView";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiError, generatePostEventReport, type PostEventReportResponse } from "@/lib/api";
import { useFirebaseAuthState } from "@/lib/auth";
import { useCommandStore } from "@/lib/stores/useCommandStore";

function errorText(error: unknown): string {
  if (error instanceof ApiError) {
    return error.body;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Post-event report generation failed.";
}


function isIncidentId(value: string): boolean {
  return /^SS-?INC[-A-Z0-9]*$/i.test(value.trim());
}

export default function PostEventLearningPage() {
  const { selectedEventId } = useCommandStore();
  const { user, ready: authReady } = useFirebaseAuthState();
  const [eventId, setEventId] = useState("");
  const incidentIdError = isIncidentId(eventId) ? "This is an incident ID. Post-event learning needs a real event ID like SS-EVT-XXXXXXXX, created after admin escalation." : null;

  useEffect(() => {
    if (!eventId && selectedEventId) {
      setEventId(selectedEventId);
    }
  }, [eventId, selectedEventId]);

  const reportMutation = useMutation<PostEventReportResponse, unknown, string>({
    mutationFn: (targetEventId) => generatePostEventReport(targetEventId)
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!user || !eventId.trim() || incidentIdError) {
      return;
    }
    reportMutation.mutate(eventId.trim());
  }

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="rounded-[28px] border border-line/80 bg-panel/90 p-8 shadow-panel">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">Post-event learning</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
                Turn event outcomes into the next playbook.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
                Generate an after-action learning report from the stored event, prediction, recommendation,
                citizen report, and live escalation timeline.
              </p>
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.34fr_0.66fr]">
          <div className="space-y-5">
            <AuthPanel
              preferredRole="control_room"
              title="Learning review sign-in"
              note="Post-event learning is an internal workflow. Backend event assignment and Firebase role checks still decide access."
            />

            <form onSubmit={handleSubmit} className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Generate report</p>
              <label className="mt-4 block text-sm text-muted">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Event ID</span>
                <input
                  value={eventId}
                  onChange={(event) => setEventId(event.target.value)}
                  placeholder="SS-EVT-XXXXXXXX or FKID000001"
                  className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                />
              </label>
              {incidentIdError ? <p className="mt-3 text-sm leading-6 text-danger">{incidentIdError}</p> : null}
              <button
                type="submit"
                disabled={!user || reportMutation.isPending || !eventId.trim() || Boolean(incidentIdError)}
                className="mt-4 rounded-2xl border border-accent/50 bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
              >
                {reportMutation.isPending ? "Generating" : "Generate post-event report"}
              </button>
              {!authReady ? <p className="mt-4 text-sm text-muted">Restoring internal session...</p> : null}
              {authReady && !user ? <p className="mt-4 text-sm text-muted">Sign in to run protected learning reviews.</p> : null}
              {reportMutation.isError ? (
                <p className="mt-4 text-sm leading-7 text-danger">{errorText(reportMutation.error)}</p>
              ) : null}
            </form>
          </div>

          {reportMutation.isPending ? (
            <section className="rounded-[24px] border border-line/70 bg-panel/85 p-6 shadow-panel space-y-5 animate-pulse">
              <div className="h-3 w-40 rounded bg-line/50" />
              <div className="h-7 w-64 rounded bg-line/60" />
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="rounded-2xl border border-line/70 bg-bg/60 p-5 space-y-3">
                    <div className="h-4 w-36 rounded bg-line/60" />
                    <div className={`h-3 rounded bg-line/40 ${i % 2 === 0 ? 'w-full' : 'w-4/5'}`} />
                    <div className="h-3 w-3/4 rounded bg-line/30" />
                  </div>
                ))}
              </div>
            </section>
          ) : (
            <PostEventReportView report={reportMutation.data} />
          )}
        </section>
      </div>
    </main>
  );
}
"use client";

import { type FormEvent, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { isFirebaseConfigured } from "@/lib/firebase";
import { loginWithFirebase, logoutFirebase, useFirebaseAuthState } from "@/lib/auth";
import { type AccessLevel, useSessionStore } from "@/lib/stores/useSessionStore";

const roleLabels: Record<AccessLevel, string> = {
  admin: "Admin",
  control_room: "Control room",
  police_officer: "Police officer",
  citizen: "Citizen",
  public_citizen: "Public citizen"
};

type AuthPanelProps = {
  preferredRole: Exclude<AccessLevel, "public_citizen">;
  title: string;
  note: string;
};

function errorText(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Firebase sign-in failed.";
}

export function AuthPanel({ preferredRole, title, note }: AuthPanelProps) {
  const queryClient = useQueryClient();
  const session = useSessionStore();
  const { user, ready } = useFirebaseAuthState();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Exclude<AccessLevel, "public_citizen">>(preferredRole);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);

    try {
      const result = await loginWithFirebase(email, password);
      session.setFirebaseSession({
        accessLevel: role,
        firebaseIdToken: result.idToken,
        firebaseUid: result.uid,
        email: result.email
      });
      await queryClient.invalidateQueries();
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setPending(false);
    }
  }

  async function handleLogout() {
    await logoutFirebase();
    session.clearSession();
    await queryClient.invalidateQueries();
  }

  return (
    <section className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
      <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Firebase access</p>
      <h2 className="mt-2 text-2xl font-semibold">{title}</h2>
      <p className="mt-3 text-sm leading-7 text-muted">{note}</p>

      {!isFirebaseConfigured ? (
        <div className="mt-5 rounded-2xl border border-warn/30 bg-warn/10 p-4 text-sm leading-7 text-warn">
          Firebase web config is not present. Public pages still work, but internal API calls need Firebase setup.
        </div>
      ) : !ready ? (
        <div className="mt-5 rounded-2xl border border-line/70 bg-bg/60 p-4 text-sm leading-7 text-muted">
          Restoring the saved Firebase session...
        </div>
      ) : user ? (
        <div className="mt-5 space-y-3">
          <div className="rounded-2xl border border-line/70 bg-bg/60 p-4 text-sm leading-7 text-copy">
            <p>Signed in: {user.email ?? user.uid}</p>
            <p>Selected UI role: {roleLabels[session.accessLevel]}</p>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy"
          >
            Sign out
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="mt-5 grid gap-4">
          <label className="text-sm text-muted">
            <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
            />
          </label>
          <label className="text-sm text-muted">
            <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
            />
          </label>
          <label className="text-sm text-muted">
            <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">UI role hint</span>
            <select
              value={role}
              onChange={(event) => setRole(event.target.value as Exclude<AccessLevel, "public_citizen">)}
              className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
            >
              <option value="admin">Admin</option>
              <option value="control_room">Control room</option>
              <option value="police_officer">Police officer</option>
              <option value="citizen">Citizen</option>
            </select>
          </label>
          <button
            type="submit"
            disabled={pending}
            className="rounded-2xl border border-accent/50 bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
          >
            {pending ? "Signing in" : "Sign in"}
          </button>
          {error ? <p className="text-sm leading-6 text-danger">{error}</p> : null}
        </form>
      )}
    </section>
  );
}

export default AuthPanel;

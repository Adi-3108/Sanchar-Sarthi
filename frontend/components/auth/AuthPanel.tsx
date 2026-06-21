"use client";

import { type FormEvent, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { getCurrentFirebaseToken, loginWithFirebase, logoutFirebase, registerWithFirebase, resendVerificationEmail, useFirebaseAuthState } from "@/lib/auth";
import { getCurrentAccess } from "@/lib/api";
import { isFirebaseConfigured } from "@/lib/firebase";
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
    if (error.message === "UNVERIFIED_EMAIL") {
      return "Please verify your email address before signing in.";
    }
    if (error.message.includes("auth/invalid-credential") || error.message.includes("auth/user-not-found") || error.message.includes("auth/wrong-password")) {
      return "Account not found or invalid credentials. Would you like to sign up?";
    }
    return error.message;
  }
  return "Firebase sign-in failed.";
}

function normalizeBackendRole(role: string): Exclude<AccessLevel, "public_citizen"> {
  if (role === "admin") return "admin";
  if (role === "control_room" || role === "control_room_officer") return "control_room";
  if (role === "police_officer") return "police_officer";
  return "citizen";
}

function resolveInteractiveRole(
  accessLevel: AccessLevel,
  preferredRole: Exclude<AccessLevel, "public_citizen">
): Exclude<AccessLevel, "public_citizen"> {
  return accessLevel === "public_citizen" ? preferredRole : accessLevel as Exclude<AccessLevel, "public_citizen">;
}

export function AuthPanel({ preferredRole, title, note }: AuthPanelProps) {
  const queryClient = useQueryClient();
  const session = useSessionStore();
  const { user, ready } = useFirebaseAuthState();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);
  const [isUnverified, setIsUnverified] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [loginSuccess, setLoginSuccess] = useState(false);
  const [role, setRole] = useState<Exclude<AccessLevel, "public_citizen">>(
    resolveInteractiveRole(session.accessLevel, preferredRole)
  );

  useEffect(() => {
    const resolvedRole = resolveInteractiveRole(session.accessLevel, preferredRole);
    setRole(resolvedRole);
  }, [preferredRole, session.accessLevel]);

  useEffect(() => {
    if (!ready) {
      return;
    }

    if (!user) {
      if (session.accessLevel !== "public_citizen" || session.firebaseUid || session.email || session.firebaseIdToken) {
        session.clearSession();
      }
      return;
    }

    if (
      session.firebaseUid === user.uid && 
      session.email === user.email && 
      session.firebaseIdToken &&
      session.accessLevel === resolveInteractiveRole(session.accessLevel, role)
    ) {
      return;
    }

    let cancelled = false;
    void (async () => {
      const idToken = (await getCurrentFirebaseToken()) ?? (await user.getIdToken());
      if (cancelled) {
        return;
      }
      const access = await getCurrentAccess(idToken);
      session.setFirebaseSession({
        accessLevel: normalizeBackendRole(access.role),
        firebaseIdToken: idToken,
        firebaseUid: user.uid,
        email: user.email
      });
    })();

    return () => {
      cancelled = true;
    };
  }, [ready, session, user]);

  async function handleResendVerification() {
    setPending(true);
    setError(null);
    try {
      await resendVerificationEmail(email, password);
      setResendSuccess(true);
      setError("A new verification link has been sent to your email. Please check your inbox.");
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setPending(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setIsUnverified(false);
    setResendSuccess(false);

    try {
      if (isSignUp) {
        await registerWithFirebase(email, password);
        setIsUnverified(true);
        setError("Account created! A verification link has been sent to your email. Please verify before signing in.");
        setIsSignUp(false);
        setPending(false);
        return;
      }

      const result = await loginWithFirebase(email, password);
      const access = await getCurrentAccess(result.idToken);
      session.setFirebaseSession({
        accessLevel: normalizeBackendRole(access.role),
        firebaseIdToken: result.idToken,
        firebaseUid: result.uid,
        email: result.email
      });
      session.setLoginSuccess(true);
      await queryClient.invalidateQueries();
    } catch (caught) {
      if (caught instanceof Error && caught.message === "UNVERIFIED_EMAIL") {
        setIsUnverified(true);
      }
      setError(errorText(caught));
    } finally {
      setPending(false);
    }
  }

  async function handleLogout() {
    await logoutFirebase();
    session.clearSession();
    setLoginSuccess(false);
    await queryClient.invalidateQueries();
  }

  const visibleRole = session.accessLevel;

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
          {loginSuccess && (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-7 text-emerald-800 shadow-sm animate-in fade-in zoom-in-95">
              <p className="font-semibold flex items-center gap-2">
                <svg className="h-5 w-5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Login Successful!
              </p>
            </div>
          )}
          <div className="rounded-2xl border border-line/70 bg-bg/60 p-4 text-sm leading-7 text-copy">
            <p>Signed in: {user.email ?? user.uid}</p>
            <p>Selected UI role: {roleLabels[visibleRole]}</p>
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
          <button
            type="submit"
            disabled={pending}
            className="rounded-2xl border border-accent/50 bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
          >
            {pending ? (isSignUp ? "Creating account..." : "Signing in...") : (isSignUp ? "Create account" : "Sign in")}
          </button>
          
          <div className="text-center mt-2">
            <button
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp);
                setError(null);
              }}
              className="text-sm text-accent hover:underline focus:outline-none"
            >
              {isSignUp ? "Already have an account? Sign in" : "Don't have an account? Sign up"}
            </button>
          </div>
          
          {error && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
              <div className="relative w-full max-w-sm rounded-3xl border border-line bg-panel p-6 shadow-xl animate-in zoom-in-95 duration-200">
                <div className="flex flex-col items-center text-center">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-danger/10 text-danger">
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-bold text-copy">Authentication Error</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted">{error}</p>
                  <div className="mt-6 flex w-full flex-col gap-3">
                    {error.includes("Would you like to sign up") && !isSignUp ? (
                      <button
                        type="button"
                        onClick={() => {
                          setError(null);
                          setIsSignUp(true);
                        }}
                        className="w-full rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-white transition hover:bg-accentSoft"
                      >
                        Sign Up Now
                      </button>
                    ) : null}
                    {isUnverified && !resendSuccess ? (
                      <button
                        type="button"
                        onClick={handleResendVerification}
                        disabled={pending}
                        className="w-full rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-white transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {pending ? "Sending..." : "Resend Verification Email"}
                      </button>
                    ) : null}
                    <button
                      type="button"
                      onClick={() => setError(null)}
                      className="w-full rounded-2xl border border-line bg-bg/50 px-4 py-3 text-sm font-semibold text-copy transition hover:bg-line/30"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </form>
      )}
    </section>
  );
}

export default AuthPanel;

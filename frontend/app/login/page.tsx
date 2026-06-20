"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import AuthPanel from "@/components/auth/AuthPanel";
import { useFirebaseAuthState } from "@/lib/auth";

export default function LoginPage() {
  const { user, ready } = useFirebaseAuthState();
  const router = useRouter();

  useEffect(() => {
    if (ready && user) {
      router.push("/user");
    }
  }, [user, ready, router]);

  return (
    <main className="min-h-screen bg-bg text-copy flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <AuthPanel 
          preferredRole="citizen" 
          title="Sign in to Sanchar Sarthi" 
          note="Sign in to report traffic incidents, vote on reports, and access personalized route recommendations." 
        />
      </div>
    </main>
  );
}

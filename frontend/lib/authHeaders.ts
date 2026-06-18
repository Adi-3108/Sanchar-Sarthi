import { getCurrentFirebaseToken } from "@/lib/auth";

export async function authHeaders(): Promise<HeadersInit> {
  const token = await getCurrentFirebaseToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
}

import { toast } from "sonner";
import { ApiError } from "@/lib/api";

function getApiMessage(body: string, defaultMessage: string): string {
  if (!body) return defaultMessage;
  try {
    const data = JSON.parse(body);
    if (data?.error?.message) return data.error.message;
    if (data?.detail) {
      if (typeof data.detail === "string") return data.detail;
      if (Array.isArray(data.detail) && data.detail[0]?.msg) return data.detail[0].msg;
    }
    if (data?.message) return data.message;
  } catch (e) {
    if (!body.trim().startsWith("<")) return body;
  }
  return defaultMessage;
}

export function handleError(error: unknown, defaultMessage = "Action failed.") {
  if (error instanceof ApiError) {
    toast.error(getApiMessage(error.body, defaultMessage));
    return;
  }
  if (error instanceof Error) {
    if (error.message === "UNVERIFIED_EMAIL") {
      toast.error("Please verify your email address before signing in.");
      return;
    }
    if (
      error.message.includes("auth/invalid-credential") ||
      error.message.includes("auth/user-not-found") ||
      error.message.includes("auth/wrong-password")
    ) {
      toast.error("Account not found or invalid credentials.");
      return;
    }
    toast.error(error.message);
    return;
  }
  toast.error(defaultMessage);
}

export function errorText(error: unknown, defaultMessage = "Action failed."): string {
  if (error instanceof ApiError) {
    return getApiMessage(error.body, defaultMessage);
  }
  if (error instanceof Error) {
    if (error.message === "UNVERIFIED_EMAIL") {
      return "Please verify your email address before signing in.";
    }
    if (
      error.message.includes("auth/invalid-credential") ||
      error.message.includes("auth/user-not-found") ||
      error.message.includes("auth/wrong-password")
    ) {
      return "Account not found or invalid credentials. Would you like to sign up?";
    }
    return error.message;
  }
  return defaultMessage;
}

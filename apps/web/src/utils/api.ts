import { ApiErrorPayload } from "@personal-finances/contracts";

export const API_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:4000/api";

export async function requestJson<T>(
  url: string,
  init: RequestInit,
  context: string,
): Promise<T> {
  const response = await fetch(url, init);

  let payload: ApiErrorPayload | null = null;
  try {
    payload = (await response.json()) as ApiErrorPayload;
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new Error(buildApiErrorMessage(context, response.status, payload));
  }

  return payload as T;
}

function normalizeApiMessage(payload: ApiErrorPayload | null): string | null {
  if (!payload?.message) {
    return null;
  }

  if (Array.isArray(payload.message)) {
    return payload.message.join("; ");
  }

  return payload.message;
}

function buildApiErrorMessage(
  context: string,
  status: number,
  payload: ApiErrorPayload | null,
): string {
  const apiMessage = normalizeApiMessage(payload);

  if (status === 401) {
    return (
      apiMessage ??
      "Session expired or invalid credentials. Please login again."
    );
  }

  if (status === 400) {
    return apiMessage ?? `Invalid request while ${context}.`;
  }

  if (status === 503) {
    return (
      apiMessage ??
      "Service is temporarily unavailable. Check API/Plaid configuration."
    );
  }

  if (status >= 500) {
    return apiMessage ?? `Server error while ${context}.`;
  }

  return apiMessage ?? `${context} failed (HTTP ${status}).`;
}

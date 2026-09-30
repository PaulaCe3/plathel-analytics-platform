import { t } from "@/lib/i18n";
import type { components } from "@/types/api.generated";
export type ErrorEnvelope = components["schemas"]["ErrorResponse"];

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

export class ApiClientError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly payload?: ErrorEnvelope,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

async function apiResponse(path: string, init: RequestInit = {}): Promise<Response> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    let payload: ErrorEnvelope | undefined;
    try {
      payload = (await response.json()) as ErrorEnvelope;
    } catch {
      payload = undefined;
    }
    if (typeof window !== "undefined" && ["DATASET_EXPIRED", "DATASET_NOT_FOUND"].includes(payload?.error?.code ?? "")) window.dispatchEvent(new Event("dataset-session-ended"));
    throw new ApiClientError(
      payload?.error?.message ?? t("client.text1"),
      response.status,
      payload,
    );
  }

  return response;
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await apiResponse(path, init);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function apiDownload(path: string, init: RequestInit = {}): Promise<{ blob: Blob; filename: string }> {
  const response = await apiResponse(path, { ...init, headers: { Accept: "application/octet-stream", ...init.headers } });
  const proposed = response.headers.get("Content-Disposition")?.match(/filename="([^"]+)"/)?.[1];
  const filename = proposed && /^[a-z0-9._-]+$/i.test(proposed) ? proposed : "datos";
  return { blob: await response.blob(), filename };
}

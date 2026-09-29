export type ErrorEnvelope = {
  error: {
    code: string;
    message: string;
    details: Array<Record<string, unknown>>;
    request_id: string;
  };
};

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

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
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
    throw new ApiClientError(
      payload?.error.message ?? "No se pudo completar la solicitud.",
      response.status,
      payload,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

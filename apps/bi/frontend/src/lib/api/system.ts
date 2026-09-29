import type { paths } from "@/types/api.generated";

import { apiRequest } from "./client";

export type HealthResponse =
  paths["/api/v1/health"]["get"]["responses"][200]["content"]["application/json"];
export type MetaResponse =
  paths["/api/v1/meta"]["get"]["responses"][200]["content"]["application/json"];

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/api/v1/health", { signal });
}

export function getMeta(signal?: AbortSignal): Promise<MetaResponse> {
  return apiRequest<MetaResponse>("/api/v1/meta", { signal });
}

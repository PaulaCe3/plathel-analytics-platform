import { apiRequest } from "./client";
import type { components } from "@/types/api.generated";

export type DashboardRequest = components["schemas"]["DashboardRequest"];
export type DashboardResponse = components["schemas"]["DashboardResponse"];
export type FilterClause = components["schemas"]["FilterClause"];

export function getDashboard(datasetId: string, request: DashboardRequest) {
  return apiRequest<DashboardResponse>(`/api/v1/datasets/${datasetId}/dashboard`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(request),
  });
}

export function getFilterOptions(datasetId: string, field: string, q = "") {
  return apiRequest<components["schemas"]["FilterOptionsResponse"]>(`/api/v1/datasets/${datasetId}/filters/${encodeURIComponent(field)}/options?q=${encodeURIComponent(q)}&limit=50`);
}

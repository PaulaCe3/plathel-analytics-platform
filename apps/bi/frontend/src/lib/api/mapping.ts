import type { components } from "@/types/api.generated";

import { apiRequest } from "./client";

export type MappingView = components["schemas"]["MappingResponse"];
export type ColumnMapping = components["schemas"]["ColumnMapping"];

export function getMapping(datasetId: string): Promise<MappingView> {
  return apiRequest<MappingView>(`/api/v1/datasets/${datasetId}/mapping`);
}

export function changeDatasetProfile(datasetId: string, profileId: string): Promise<void> {
  return apiRequest(`/api/v1/datasets/${datasetId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ industry_id: profileId }),
  });
}

export function saveMapping(datasetId: string, profileId: string, mappings: ColumnMapping[]): Promise<MappingView> {
  return apiRequest<MappingView>(`/api/v1/datasets/${datasetId}/mapping`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile_id: profileId, mappings }),
  });
}

import type { components } from "@/types/api.generated";

import { apiRequest } from "./client";

export type Dataset = components["schemas"]["DatasetResponse"];
export type DatasetPreview = components["schemas"]["PreviewResponse"];

export async function uploadDataset(file: File): Promise<Dataset> {
  const body = new FormData();
  body.append("file", file);
  return apiRequest<Dataset>("/api/v1/datasets", { method: "POST", body });
}

export function getDatasetPreview(datasetId: string): Promise<DatasetPreview> {
  return apiRequest<DatasetPreview>(`/api/v1/datasets/${datasetId}/preview?rows=50`);
}

export function selectDatasetSheet(datasetId: string, sheet: string): Promise<Dataset> {
  return apiRequest<Dataset>(`/api/v1/datasets/${datasetId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sheet }),
  });
}

export function deleteDataset(datasetId: string): Promise<void> {
  return apiRequest<void>(`/api/v1/datasets/${datasetId}`, { method: "DELETE" });
}

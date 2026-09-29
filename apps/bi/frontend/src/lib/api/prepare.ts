import type { components } from "@/types/api.generated";

import { apiRequest } from "./client";

export type ValidateResult = components["schemas"]["ValidateResponse"];
export type CleaningResult = components["schemas"]["CleaningResponse"];
export type CleaningAction = components["schemas"]["CleaningActionSpec"];
export type TransformationLog = components["schemas"]["TransformationLog"];

export function validateDataset(datasetId: string): Promise<ValidateResult> {
  return apiRequest<ValidateResult>(`/api/v1/datasets/${datasetId}/validate`, { method: "POST" });
}

export function applyCleaning(datasetId: string, actions: CleaningAction[]): Promise<CleaningResult> {
  return apiRequest<CleaningResult>(`/api/v1/datasets/${datasetId}/cleaning`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actions }),
  });
}

export function getTransformations(datasetId: string): Promise<TransformationLog> {
  return apiRequest<TransformationLog>(`/api/v1/datasets/${datasetId}/transformations`);
}

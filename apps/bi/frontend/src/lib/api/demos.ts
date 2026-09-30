import type { components } from "@/types/api.generated";
import { apiRequest } from "./client";
import type { Dataset } from "./datasets";

export type DemoSummary = components["schemas"]["DemoSummary"];

export function getDemos(): Promise<DemoSummary[]> {
  return apiRequest("/api/v1/demos");
}

export function createDemo(demoId: string): Promise<Dataset> {
  return apiRequest("/api/v1/datasets/demo", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ demo_id: demoId }) });
}

import type { components } from "@/types/api.generated";
import { apiDownload } from "./client";

export type ExportOptions = components["schemas"]["ExportOptions"];

export async function downloadDataset(datasetId: string, options: ExportOptions): Promise<void> {
  const { blob, filename } = await apiDownload(`/api/v1/datasets/${datasetId}/export`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(options),
  });
  const url = URL.createObjectURL(blob);
  try {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    try { link.click(); } finally { link.remove(); }
  } finally {
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

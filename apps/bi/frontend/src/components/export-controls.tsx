"use client";
import { useState } from "react";
import type { FilterClause } from "@/lib/api/dashboard";
import { downloadDataset, ExportOptions } from "@/lib/api/exports";

export function ExportControls({ datasetId, filters, disabled = false }: { datasetId: string; filters: FilterClause[]; disabled?: boolean }) {
  const [format, setFormat] = useState("csv");
  const [scope, setScope] = useState<ExportOptions["scope"]>("filtered_data");
  const [headers, setHeaders] = useState<ExportOptions["headers"]>("friendly");
  const [original, setOriginal] = useState(false);
  const [ignored, setIgnored] = useState(false);
  const [transformations, setTransformations] = useState(true);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  async function download() {
    setBusy(true); setStatus("Preparando descarga…");
    try {
      await downloadDataset(datasetId, { format, scope, headers, filters: scope === "filtered_data" ? filters : [], include_original_columns: original, include_ignored_columns: ignored, include_transformations: transformations });
      setStatus("Descarga iniciada.");
    } catch (error) { setStatus(error instanceof Error ? error.message : "No se pudo exportar."); }
    finally { setBusy(false); }
  }
  return <details className="rounded-2xl border border-slate-200 bg-white p-5">
    <summary className="cursor-pointer font-semibold">Exportar</summary>
    <div className="mt-4 flex flex-wrap gap-4">
      <label>Formato <select aria-label="Formato de exportación" value={format} onChange={(event) => setFormat(event.target.value)} className="ml-2 rounded-lg border p-2"><option value="csv">CSV</option><option value="xlsx">XLSX</option></select></label>
      <label>Alcance <select aria-label="Alcance de exportación" value={scope} onChange={(event) => setScope(event.target.value as ExportOptions["scope"])} className="ml-2 rounded-lg border p-2"><option value="clean_data">Datos limpios</option><option value="filtered_data">Datos filtrados</option></select></label>
      <label>Encabezados <select aria-label="Encabezados de exportación" value={headers} onChange={(event) => setHeaders(event.target.value as ExportOptions["headers"])} className="ml-2 rounded-lg border p-2"><option value="friendly">Amigables</option><option value="original">Originales</option></select></label>
    </div>
    <div className="my-4 flex flex-wrap gap-4">
      <label><input type="checkbox" checked={original} onChange={(event) => setOriginal(event.target.checked)} /> Columnas originales</label>
      <label><input type="checkbox" checked={ignored} onChange={(event) => setIgnored(event.target.checked)} /> Columnas ignoradas</label>
      <label><input type="checkbox" disabled={format !== "xlsx"} checked={transformations} onChange={(event) => setTransformations(event.target.checked)} /> Registro de cambios (XLSX)</label>
    </div>
    <button onClick={download} disabled={busy || disabled} className="rounded-xl bg-slate-950 px-5 py-3 font-semibold text-white disabled:opacity-40">{busy ? "Exportando…" : "Descargar"}</button>
    <p role="status" className="mt-3 text-sm">{disabled ? "Esperá a que el dashboard termine de aplicar los filtros." : status}</p>
  </details>;
}

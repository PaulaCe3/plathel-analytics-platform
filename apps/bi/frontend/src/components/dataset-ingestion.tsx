"use client";

import { FormEvent, useState } from "react";

import {
  Dataset,
  DatasetPreview,
  deleteDataset,
  getDatasetPreview,
  selectDatasetSheet,
  uploadDataset,
} from "@/lib/api/datasets";

export function DatasetIngestion() {
  const [file, setFile] = useState<File | null>(null);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [status, setStatus] = useState("Seleccioná un CSV o XLSX para comenzar.");
  const [busy, setBusy] = useState(false);

  async function refreshPreview(current: Dataset) {
    setPreview(await getDatasetPreview(current.dataset_id));
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setStatus("Subiendo y validando el archivo…");
    try {
      const created = await uploadDataset(file);
      setDataset(created);
      await refreshPreview(created);
      setStatus("Dataset listo para revisar.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "No se pudo subir el archivo.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSheet(sheet: string) {
    if (!dataset) return;
    setBusy(true);
    setStatus("Cambiando la hoja…");
    try {
      const updated = await selectDatasetSheet(dataset.dataset_id, sheet);
      setDataset(updated);
      await refreshPreview(updated);
      setStatus("Hoja actualizada.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "No se pudo cambiar la hoja.");
    } finally {
      setBusy(false);
    }
  }

  async function clearDataset() {
    if (dataset) await deleteDataset(dataset.dataset_id);
    setDataset(null);
    setPreview(null);
    setFile(null);
    setStatus("La sesión fue eliminada.");
  }

  return (
    <div className="space-y-8">
      <form onSubmit={handleUpload} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <label className="block text-sm font-semibold text-slate-800" htmlFor="dataset-file">Archivo de datos</label>
        <input
          id="dataset-file"
          type="file"
          accept=".csv,.xlsx"
          className="mt-3 block w-full rounded-xl border border-slate-300 p-3 text-sm"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button disabled={!file || busy} className="rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-40">{busy ? "Procesando…" : "Subir archivo"}</button>
          <span role="status" className="text-sm text-slate-600">{status}</span>
        </div>
      </form>

      {dataset && preview && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-950">Vista previa</h2>
              <p className="mt-1 text-sm text-slate-600">{dataset.row_count} filas · {dataset.column_count} columnas</p>
            </div>
            <button onClick={clearDataset} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">Eliminar sesión</button>
          </div>

          {dataset.available_sheets.length > 1 && (
            <label className="mt-6 block text-sm font-medium text-slate-700">
              Hoja
              <select value={dataset.selected_sheet ?? ""} onChange={(event) => handleSheet(event.target.value)} disabled={busy} className="ml-3 rounded-lg border border-slate-300 px-3 py-2">
                {dataset.available_sheets.map((sheet) => <option key={sheet}>{sheet}</option>)}
              </select>
            </label>
          )}

          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full border-collapse text-left text-sm">
              <thead><tr>{preview.columns.map((column) => <th key={column.key} className="border-b border-slate-200 px-3 py-2 font-semibold">{column.original_name || column.key}</th>)}</tr></thead>
              <tbody>{preview.rows.map((row, index) => <tr key={index}>{preview.columns.map((column) => <td key={column.key} className="max-w-64 truncate border-b border-slate-100 px-3 py-2 text-slate-700">{row[column.key] ?? "—"}</td>)}</tr>)}</tbody>
            </table>
          </div>
          <a href={`/bi/${dataset.dataset_id}/mapping`} className="mt-6 inline-flex rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white">Seleccionar rubro y mapear columnas</a>
        </section>
      )}
    </div>
  );
}

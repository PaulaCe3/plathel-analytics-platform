"use client";
import { t } from "@/lib/i18n";

import { FormEvent, useState, useRef, useEffect } from "react";

import {
  Dataset,
  DatasetPreview,
  deleteDataset,
  getDatasetPreview,
  selectDatasetSheet,
  uploadDataset,
} from "@/lib/api/datasets";

import { getMeta } from "@/lib/api/system";
import { ApiClientError } from "@/lib/api/client";
import { HomeIcon } from "@/components/home-sections";

export function DatasetIngestion() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [status, setStatus] = useState(t("dataset-ingestion.action3"));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [maxMb, setMaxMb] = useState<number | null>(null);
  const [dragging, setDragging] = useState(false);
  function loadLimit() { getMeta().then(meta => {setMaxMb(meta.max_file_mb);setError("");}).catch(()=>setError(t("home.metaError"))); }
  useEffect(()=>{getMeta().then(meta=>setMaxMb(meta.max_file_mb)).catch(()=>setError(t("home.metaError")));},[]);
  function chooseFile(candidate: File | null) {
    if(busy || dataset) return;
    setError(""); setFile(null);
    if(!candidate) return;
    if(!/\.(csv|xlsx)$/i.test(candidate.name)) {setError(t("home.unreadable"));return;}
    if(maxMb != null && candidate.size > maxMb * 1024 * 1024) {setError(`${t("home.tooLarge")} ${maxMb} MB.`);return;}
    setFile(candidate); setStatus("");
  }
  const safeName = file?.name.split(/[\\/]/).pop()?.replace(/[\u0000-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069]/g, "") ?? "";


  async function refreshPreview(current: Dataset) {
    setPreview(await getDatasetPreview(current.dataset_id));
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    if (!file || busy || maxMb == null) return;
    if(file.size > maxMb * 1024 * 1024) {setError(`${t("home.tooLarge")} ${maxMb} MB.`);return;}
    setError("");
    setBusy(true);
    setStatus(t("home.preparing"));
    try {
      const created = await uploadDataset(file);
      setDataset(created);
      await refreshPreview(created);
      setStatus(t("dataset-ingestion.status1"));
    } catch (error) {
      setError(error instanceof ApiClientError && error.status === 429 ? error.message : error instanceof ApiClientError && error.status === 413 ? `${t("home.tooLarge")} ${maxMb} MB.` : t("home.unreadable"));
      setStatus("");
    } finally {
      setBusy(false);
    }
  }

  async function handleSheet(sheet: string) {
    if (!dataset) return;
    setBusy(true);
    setStatus(t("dataset-ingestion.text3"));
    try {
      const updated = await selectDatasetSheet(dataset.dataset_id, sheet);
      setDataset(updated);
      await refreshPreview(updated);
      setStatus(t("dataset-ingestion.status2"));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : t("dataset-ingestion.text4"));
    } finally {
      setBusy(false);
    }
  }

  async function clearDataset() {
    setBusy(true);
    try {
      if (dataset) await deleteDataset(dataset.dataset_id);
      setDataset(null); setPreview(null); setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      setStatus(t("session.deleted"));
    } catch (error) { setStatus(error instanceof Error ? error.message : t("request.failed")); }
    finally { setBusy(false); }
  }

  return (
    <div className="space-y-8">
      <section id="upload" tabIndex={-1} className="home-upload" aria-labelledby="upload-title">
      <h2 id="upload-title" className="sr-only">{t("home.upload")}</h2>
      <form onSubmit={handleUpload} aria-busy={busy}>
        <input ref={inputRef} id="dataset-file" type="file" accept=".csv,.xlsx" className="sr-only" tabIndex={-1} aria-label={t("dataset-ingestion.text5")} disabled={busy || !!dataset} onChange={event=>chooseFile(event.target.files?.[0] ?? null)}/>
        <div className="home-dropzone" data-dragging={dragging} onDragOver={event=>{event.preventDefault();if(!busy && !dataset)setDragging(true);}} onDragLeave={()=>setDragging(false)} onDrop={event=>{event.preventDefault();setDragging(false);chooseFile(event.dataTransfer.files[0] ?? null);}}>
          <HomeIcon kind="upload"/>
          {file ? <><strong><span aria-hidden="true">✓ </span>{safeName}</strong><p>{new Intl.NumberFormat("es-AR",{maximumFractionDigits:2}).format(file.size / 1024 / 1024)} MB</p><div className="home-file-actions"><button type="submit" className="home-primary" disabled={busy || !!dataset || maxMb == null}>{busy ? t("home.preparing") : t("home.continue")}</button><button type="button" className="home-secondary" disabled={busy || !!dataset} onClick={()=>{if(inputRef.current){inputRef.current.value="";inputRef.current.click();}}}>{t("home.change")}</button></div></> : <><strong>{t("home.drop")}</strong><p>{t("home.or")}</p><button type="button" className="home-primary" disabled={busy} onClick={()=>inputRef.current?.click()}>{t("home.select")}</button></>}
          <p>{t("home.format")}{maxMb != null ? ` · ${t("home.limit")} ${maxMb} MB` : ""}</p>
        </div>
        <div role="status" aria-live="polite" className="home-feedback">{busy ? <span className="home-loading"><span aria-hidden="true" className="home-spinner"/>{t("home.preparing")}</span> : file ? status : ""}</div>
        {error && <p role="alert" className="home-feedback home-error">{error} {maxMb == null && <button type="button" className="home-secondary" onClick={loadLimit}>{t("home.retry")}</button>}</p>}
      </form>
      </section>

      {dataset && preview && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-950">{t("home.preview")}</h2>
              <p className="mt-1 text-sm text-slate-600">{dataset.row_count}{t("dataset-ingestion.text7")}{dataset.column_count}{t("dataset-ingestion.text8")}</p>
            </div>
            <button disabled={busy} onClick={clearDataset} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">{t("dataset-ingestion.text9")}</button>
          </div>

          {dataset.available_sheets.length > 1 && (
            <label className="mt-6 block text-sm font-medium text-slate-700">{t("dataset-ingestion.text10")}<select value={dataset.selected_sheet ?? ""} onChange={(event) => handleSheet(event.target.value)} disabled={busy} className="ml-3 rounded-lg border border-slate-300 px-3 py-2">
                {dataset.available_sheets.map((sheet) => <option key={sheet}>{sheet}</option>)}
              </select>
            </label>
          )}

          <details className="pl-details"><summary>Ver una muestra de los datos</summary><div className="mt-6 overflow-x-auto">
            <table className="min-w-full border-collapse text-left text-sm">
              <thead><tr>{preview.columns.map((column) => <th key={column.key} className="border-b border-slate-200 px-3 py-2 font-semibold">{column.original_name || column.key}</th>)}</tr></thead>
              <tbody>{preview.rows.map((row, index) => <tr key={index}>{preview.columns.map((column) => <td key={column.key} className="max-w-64 truncate border-b border-slate-100 px-3 py-2 text-slate-700">{row[column.key] ?? "—"}</td>)}</tr>)}</tbody>
            </table>
          </div></details>
          <a href={`/bi/${dataset.dataset_id}/mapping`} className="mt-6 inline-flex rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white">{t("home.columns")}</a>
        </section>
      )}
    </div>
  );
}

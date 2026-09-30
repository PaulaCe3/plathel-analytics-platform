"use client";
import { t } from "@/lib/i18n";
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
    setBusy(true); setStatus(t("export-controls.text1"));
    try {
      await downloadDataset(datasetId, { format, scope, headers, filters: scope === "filtered_data" ? filters : [], include_original_columns: original, include_ignored_columns: ignored, include_transformations: transformations });
      setStatus(t("export-controls.text2"));
    } catch (error) { setStatus(error instanceof Error ? error.message : t("export-controls.text3")); }
    finally { setBusy(false); }
  }
  return <details className="rounded-2xl border border-slate-200 bg-white p-5">
    <summary className="cursor-pointer font-semibold">{t("export-controls.action3")}</summary>
    <div className="mt-4 flex flex-wrap gap-4">
      <label>{t("export-controls.text4")}<select aria-label={t("export-controls.text5")} value={format} onChange={(event) => setFormat(event.target.value)} className="ml-2 rounded-lg border p-2"><option value="csv">{t("export-controls.text6")}</option><option value="xlsx">{t("export-controls.text7")}</option></select></label>
      <label>{t("export-controls.text8")}<select aria-label={t("export-controls.text9")} value={scope} onChange={(event) => setScope(event.target.value as ExportOptions["scope"])} className="ml-2 rounded-lg border p-2"><option value="clean_data">{t("export-controls.text10")}</option><option value="filtered_data">{t("export-controls.text11")}</option></select></label>
      <label>{t("export-controls.text12")}<select aria-label={t("export-controls.text13")} value={headers} onChange={(event) => setHeaders(event.target.value as ExportOptions["headers"])} className="ml-2 rounded-lg border p-2"><option value="friendly">{t("export-controls.text14")}</option><option value="original">{t("export-controls.text15")}</option></select></label>
    </div>
    <div className="my-4 flex flex-wrap gap-4">
      <label><input type="checkbox" checked={original} onChange={(event) => setOriginal(event.target.checked)} />{t("export-controls.text16")}</label>
      <label><input type="checkbox" checked={ignored} onChange={(event) => setIgnored(event.target.checked)} />{t("export-controls.text17")}</label>
      <label><input type="checkbox" disabled={format !== "xlsx"} checked={transformations} onChange={(event) => setTransformations(event.target.checked)} />{t("export-controls.text18")}</label>
    </div>
    <button onClick={download} disabled={busy || disabled} className="rounded-xl bg-slate-950 px-5 py-3 font-semibold text-white disabled:opacity-40">{busy ? t("export-controls.action2") : t("export-controls.action1")}</button>
    <p role="status" className="mt-3 text-sm">{disabled ? t("export-controls.text19") : status}</p>
  </details>;
}

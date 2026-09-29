"use client";

import { useEffect, useState } from "react";

import { CleaningAction, CleaningResult, TransformationLog, ValidateResult, applyCleaning, getTransformations, validateDataset } from "@/lib/api/prepare";

export function DatasetReview({ datasetId }: { datasetId: string }) {
  const [report, setReport] = useState<ValidateResult | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [cleaned, setCleaned] = useState<CleaningResult | null>(null);
  const [log, setLog] = useState<TransformationLog | null>(null);
  const [status, setStatus] = useState("Validando el dataset…");
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    validateDataset(datasetId)
      .then((result) => {
        setReport(result);
        setSelected(new Set((result.cleaning_plan.actions ?? []).filter((action) => action.selected && !action.destructive).map((action) => action.id)));
        setStatus("Validación completada. Las filas inválidas fueron conservadas.");
      })
      .catch((error) => setStatus(error instanceof Error ? error.message : "No se pudo validar el dataset."))
      .finally(() => setBusy(false));
  }, [datasetId]);

  function toggle(action: CleaningAction) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(action.id)) next.delete(action.id); else next.add(action.id);
      return next;
    });
  }

  async function apply() {
    if (!report) return;
    const actions = (report.cleaning_plan.actions ?? []).filter((action) => selected.has(action.id));
    if (actions.some((action) => action.destructive) && !window.confirm("Seleccionaste acciones destructivas. ¿Querés aplicarlas?")) return;
    setBusy(true);
    setStatus("Reconstruyendo el dataset desde los datos originales…");
    try {
      const result = await applyCleaning(datasetId, actions);
      setCleaned(result);
      setLog(await getTransformations(datasetId));
      setStatus("Limpieza confirmada. El dataset está listo.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "No se pudo aplicar la limpieza.");
    } finally {
      setBusy(false);
    }
  }

  if (!report) return <p role="status" className="rounded-2xl bg-white p-6 shadow-sm">{status}</p>;
  const severityLabel = { error: "Error", warning: "Warning", info: "Info" };

  return <div className="space-y-6">
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Validación</p>
      <h2 className="mt-2 text-2xl font-semibold">¿Podemos analizar estos datos?</h2>
      <p className="mt-2 text-slate-700">Estado: <strong>{report.validation.valid ? "Válido" : "Requiere correcciones"}</strong>. {report.validation.blocking_count} errores, {report.validation.warning_count} warnings.</p>
      <div className="mt-4 space-y-2">{(report.validation.issues ?? []).map((issue) => <div key={issue.id} className="rounded-lg border border-slate-200 p-3 text-sm"><strong>{severityLabel[issue.severity]}:</strong> {issue.message} {issue.field_id && <span>Campo: {issue.field_id}.</span>} {issue.count != null && <span> Filas: {issue.count}.</span>}</div>)}</div>
    </section>

    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Calidad</p>
      <h2 className="mt-2 text-2xl font-semibold">Problemas encontrados</h2>
      <p className="mt-2 text-slate-700">{report.quality.summary?.total_issues ?? 0} hallazgos: {report.quality.summary?.error_count ?? 0} errores, {report.quality.summary?.warning_count ?? 0} warnings y {report.quality.summary?.info_count ?? 0} informativos.</p>
      <div className="mt-4 space-y-2">{(report.quality.issues ?? []).map((issue) => <div key={issue.id} className="rounded-lg bg-slate-50 p-3 text-sm"><strong>{severityLabel[issue.severity]} · {issue.code}</strong><p>{issue.message}</p>{issue.count != null && <p>{issue.count} casos{issue.ratio != null ? ` (${Math.round(issue.ratio * 100)} %)` : ""}. No fueron eliminados automáticamente.</p>}</div>)}</div>
    </section>

    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Limpieza</p>
      <h2 className="mt-2 text-2xl font-semibold">Modificaciones disponibles</h2>
      <div className="mt-4 space-y-3">{(report.cleaning_plan.actions ?? []).map((action) => <label key={action.id} className="flex cursor-pointer gap-3 rounded-xl border border-slate-200 p-4"><input type="checkbox" checked={selected.has(action.id)} onChange={() => toggle(action)} /><span><strong>{action.description}</strong><span className="block text-sm text-slate-600">{action.destructive ? "Destructiva · nunca preseleccionada" : "No destructiva"}</span></span></label>)}</div>
      <button disabled={busy || !report.validation.valid} onClick={apply} className="mt-5 rounded-xl bg-slate-950 px-5 py-3 font-semibold text-white disabled:opacity-40">Aplicar selección</button>
      <p role="status" className="mt-3 text-sm text-slate-600">{status}</p>
    </section>

    {(cleaned || log) && <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Auditoría</p><h2 className="mt-2 text-2xl font-semibold">Registro de cambios</h2><ol className="mt-4 space-y-3">{(log?.transformations ?? cleaned?.transformation_log.transformations ?? []).map((item) => <li key={item.id} className="rounded-lg bg-slate-50 p-3"><strong>{item.seq}. {item.summary}</strong><p className="text-sm text-slate-600">{item.rows_before} → {item.rows_after} filas · {item.automatic ? "Automática" : "Confirmada por el usuario"}</p></li>)}</ol></section>}
  </div>;
}

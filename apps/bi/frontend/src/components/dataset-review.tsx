"use client";
import { t } from "@/lib/i18n";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DemoNotice } from "./demo-notice";

import { CleaningAction, CleaningResult, TransformationLog, ValidateResult, applyCleaning, getTransformations, validateDataset } from "@/lib/api/prepare";

export function DatasetReview({ datasetId }: { datasetId: string }) {
  const [report, setReport] = useState<ValidateResult | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [cleaned, setCleaned] = useState<CleaningResult | null>(null);
  const [log, setLog] = useState<TransformationLog | null>(null);
  const [status, setStatus] = useState(t("dataset-review.action1"));
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    validateDataset(datasetId)
      .then((result) => {
        setReport(result);
        setSelected(new Set((result.cleaning_plan.actions ?? []).filter((action) => action.selected && !action.destructive).map((action) => action.id)));
        setStatus(t("dataset-review.text1"));
      })
      .catch((error) => setStatus(error instanceof Error ? error.message : t("dataset-review.text2")))
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
    if (actions.some((action) => action.destructive) && !window.confirm(t("dataset-review.text3"))) return;
    setBusy(true);
    setStatus(t("dataset-review.text4"));
    try {
      const result = await applyCleaning(datasetId, actions);
      setCleaned(result);
      setLog(await getTransformations(datasetId));
      setStatus(t("dataset-review.text5"));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : t("dataset-review.text6"));
    } finally {
      setBusy(false);
    }
  }

  if (!report) return <p role="status" className="rounded-2xl bg-white p-6 shadow-sm">{status}</p>;
  const severityLabel = { error: t("dataset-review.text7"), warning: t("dataset-review.text8"), info: t("dataset-review.text9") };

  return <div className="space-y-6">
    <DemoNotice datasetId={datasetId} />
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">{t("dataset-review.text10")}</p>
      <h2 className="mt-2 text-2xl font-semibold">{t("dataset-review.text11")}</h2>
      <p className="mt-2 text-slate-700">{t("dataset-review.text12")}<strong>{report.validation.valid ? t("dataset-review.text13") : t("dataset-review.text14")}</strong>. {report.validation.blocking_count}{t("dataset-review.text15")}{report.validation.warning_count}{t("dataset-review.text16")}</p>
      <div className="mt-4 space-y-2">{(report.validation.issues ?? []).map((issue) => <div key={issue.id} className="rounded-lg border border-slate-200 p-3 text-sm"><strong>{severityLabel[issue.severity]}:</strong> {issue.message} {issue.field_id && <span>{t("dataset-review.text17")}{issue.field_id}.</span>} {issue.count != null && <span>{t("dataset-review.text18")}{issue.count}.</span>}</div>)}</div>
    </section>

    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">{t("dataset-review.text19")}</p>
      <h2 className="mt-2 text-2xl font-semibold">{t("dataset-review.text20")}</h2>
      <p className="mt-2 text-slate-700">{report.quality.summary?.total_issues ?? 0}{t("dataset-review.text21")}{report.quality.summary?.error_count ?? 0}{t("dataset-review.text22")}{report.quality.summary?.warning_count ?? 0}{t("dataset-review.text23")}{report.quality.summary?.info_count ?? 0}{t("dataset-review.text24")}</p>
      <div className="mt-4 space-y-2">{(report.quality.issues ?? []).map((issue) => <div key={issue.id} className="rounded-lg bg-slate-50 p-3 text-sm"><strong>{severityLabel[issue.severity]} · {issue.code}</strong><p>{issue.message}</p>{issue.count != null && <p>{issue.count}{t("dataset-review.text25")}{issue.ratio != null ? ` (${Math.round(issue.ratio * 100)} %)` : ""}{t("dataset-review.text26")}</p>}</div>)}</div>
    </section>

    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">{t("dataset-review.text27")}</p>
      <h2 className="mt-2 text-2xl font-semibold">{t("dataset-review.text28")}</h2>
      <div className="mt-4 space-y-3">{(report.cleaning_plan.actions ?? []).map((action) => <label key={action.id} className="flex cursor-pointer gap-3 rounded-xl border border-slate-200 p-4"><input type="checkbox" checked={selected.has(action.id)} onChange={() => toggle(action)} /><span><strong>{action.description}</strong><span className="block text-sm text-slate-600">{action.destructive ? t("dataset-review.text29") : t("dataset-review.text30")}</span></span></label>)}</div>
      <button disabled={busy || !report.validation.valid} onClick={apply} className="mt-5 rounded-xl bg-slate-950 px-5 py-3 font-semibold text-white disabled:opacity-40">{t("dataset-review.action2")}</button>
      <p role="status" className="mt-3 text-sm text-slate-600">{status}</p>
    </section>

    {(cleaned || log) && <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-slate-600">{t("dataset-review.text31")}</p><h2 className="mt-2 text-2xl font-semibold">{t("dataset-review.text32")}</h2><ol className="mt-4 space-y-3">{(log?.transformations ?? cleaned?.transformation_log.transformations ?? []).map((item) => <li key={item.id} className="rounded-lg bg-slate-50 p-3"><strong>{item.seq}. {item.summary}</strong><p className="text-sm text-slate-600">{item.rows_before} → {item.rows_after}{t("dataset-review.text33")}{item.automatic ? t("dataset-review.text34") : t("dataset-review.text35")}</p></li>)}</ol><Link href={`/bi/${datasetId}/dashboard`} className="mt-5 inline-block rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white">{t("dataset-review.action3")}</Link></section>}
  </div>;
}

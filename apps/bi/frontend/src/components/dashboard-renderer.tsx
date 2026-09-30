"use client";

import type { components } from "@/types/api.generated";
import { EChartsBase } from "@/components/charts/echarts-base";
import { chartOption } from "@/components/charts/adapters/dashboard";

type DashboardResponse = components["schemas"]["DashboardResponse"];
type Widget = components["schemas"]["WidgetSpec"];
type Metric = components["schemas"]["MetricResult"];
type Chart = components["schemas"]["ChartResult"];
type Quality = components["schemas"]["QualityResult"];

import { messages as labels, t, insightText } from "@/lib/i18n";
import type { CSSProperties } from "react";

function title(key: string, terminology: Record<string, string>) {
  if (key.startsWith("field.") && terminology[key.slice(6)]) return terminology[key.slice(6)];
  return labels[key] ?? key.replace(/^field\./, "").replaceAll("_", t("dashboard-renderer.text1"));
}

function metricValue(metric: Metric) {
  if (metric.value == null) return "—";
  return new Intl.NumberFormat("es-AR", { style: metric.format.type === "currency" ? "currency" : metric.format.type === "percent" ? "percent" : "decimal", currency: metric.format.currency ?? "ARS", maximumFractionDigits: metric.format.decimals }).format(metric.value);
}

export function ErrorState() { return <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{t("widget.error")}</p>; }
export function EmptyState() { return <p role="status" className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">{t("widget.empty")}</p>; }

function WidgetView({ widget, value, label }: { widget: Widget; value: unknown; label: string }) {
  const base = value as { status?: string } | undefined;
  if (!base || base.status === "empty" || base.status === "unavailable") return <EmptyState />;
  if (base.status === "error") return <ErrorState />;
  if (widget.type === "kpi") {
    const metric = value as Metric;
    return <div><p className="text-3xl font-bold text-slate-950">{metricValue(metric)}</p><p className="mt-2 text-xs text-slate-600">{metric.excluded_rows}{t("dashboard-renderer.text2")}</p>{metric.comparison?.delta_pct != null && <p className="mt-2 text-sm">{new Intl.NumberFormat("es-AR", { style: "percent", maximumFractionDigits: 1 }).format(metric.comparison.delta_pct)}{t("dashboard-renderer.text3")}</p>}</div>;
  }
  if (["timeseries", "breakdown", "ranking"].includes(widget.type)) {
    const chart = value as Chart;
    return <><EChartsBase label={label} option={chartOption(chart, t(chart.series?.[0]?.label_key ?? "chart.value"))} /><details><summary>{t("chart.table")}</summary><div className="overflow-x-auto"><table className="w-full text-left text-sm"><caption className="sr-only">{label}</caption><thead><tr><th scope="col">{t("chart.category")}</th><th scope="col">{t("chart.value")}</th></tr></thead><tbody>{(chart.series ?? []).flatMap((series) => series.points.map((point, index) => <tr key={`${series.key}-${index}`}><th scope="row">{String(point[0])}</th><td>{typeof point[1] === "number" ? new Intl.NumberFormat("es-AR").format(point[1]) : String(point[1] ?? "—")}</td></tr>))}</tbody></table></div></details></>;
  }
  if (widget.type === "quality") { const q = value as Quality; return <p>{q.total_issues}{t("dashboard-renderer.text4")}{q.error_count}{t("dashboard-renderer.text5")}{q.warning_count}{t("dashboard-renderer.text6")}</p>; }
  if (widget.type === "insights") {
    const insights = (value as { insights?: Array<{ id: string; template_key: string; text?: string; params: Record<string, unknown> }> }).insights ?? [];
    return <ul className="space-y-2">{insights.map((item) => <li key={item.id} className="rounded-xl bg-amber-50 p-3">{item.text && item.text !== item.template_key ? item.text : insightText(item.template_key, item.params)}</li>)}</ul>;
  }
  return <ErrorState />;
}

export function DashboardRenderer({ dashboard }: { dashboard: DashboardResponse }) {
  const terminology = dashboard.spec.terminology ?? {};
  return <div className="space-y-8">{dashboard.spec.sections.map((section) => <section key={section.id}><h2 className="mb-4 text-2xl font-semibold">{title(section.title_key, terminology)}</h2><div className="grid grid-cols-12 gap-4">{section.widgets.map((widget) => <article key={widget.id} className="dashboard-widget min-w-0 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" style={{ "--widget-span": widget.layout.span } as CSSProperties}><h3 className="mb-4 font-semibold">{title(widget.title_key, terminology)}</h3><WidgetView label={title(widget.title_key, terminology)} widget={widget} value={dashboard.data[widget.id]} /></article>)}</div></section>)}</div>;
}

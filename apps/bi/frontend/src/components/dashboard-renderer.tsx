"use client";

import type { components } from "@/types/api.generated";
import { EChartsBase } from "@/components/charts/echarts-base";
import { chartOption } from "@/components/charts/adapters/dashboard";

type DashboardResponse = components["schemas"]["DashboardResponse"];
type Widget = components["schemas"]["WidgetSpec"];
type Metric = components["schemas"]["MetricResult"];
type Chart = components["schemas"]["ChartResult"];
type Quality = components["schemas"]["QualityResult"];

const labels: Record<string, string> = {
  "section.executive_summary": "Resumen ejecutivo", "section.insights": "Hallazgos", "section.temporal": "Evolución temporal",
  "section.breakdown": "Desgloses", "section.customers": "Clientes", "section.concept_analysis": "Análisis por concepto",
  "section.geography": "Ubicación", "section.channel": "Canales", "section.data_quality": "Calidad de datos",
  "metric.revenue": "Ingresos", "metric.transactions": "Transacciones", "metric.customers": "Clientes",
  "metric.avg_transaction_value": "Ticket promedio", "metric.quantity": "Cantidad", "metric.avg_unit_price": "Precio unitario promedio",
};

function title(key: string, terminology: Record<string, string>) {
  if (key === "field.concept") return terminology.concept ?? "Concepto";
  return labels[key] ?? key.replace(/^field\./, "").replaceAll("_", " ");
}

function metricValue(metric: Metric) {
  if (metric.value == null) return "—";
  return new Intl.NumberFormat("es-AR", { style: metric.format.type === "currency" ? "currency" : "decimal", currency: metric.format.currency ?? "ARS", maximumFractionDigits: metric.format.decimals }).format(metric.value);
}

function ErrorState() { return <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">No pudimos mostrar este bloque.</p>; }
function EmptyState() { return <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">No hay datos para los filtros seleccionados.</p>; }

function WidgetView({ widget, value }: { widget: Widget; value: unknown }) {
  const base = value as { status?: string } | undefined;
  if (!base || base.status === "empty" || base.status === "unavailable") return <EmptyState />;
  if (base.status === "error") return <ErrorState />;
  if (widget.type === "kpi") {
    const metric = value as Metric;
    return <div><p className="text-3xl font-bold text-slate-950">{metricValue(metric)}</p><p className="mt-2 text-xs text-slate-500">{metric.excluded_rows} filas excluidas</p>{metric.comparison?.delta_pct != null && <p className="mt-2 text-sm">{new Intl.NumberFormat("es-AR", { style: "percent", maximumFractionDigits: 1 }).format(metric.comparison.delta_pct)} vs. período anterior</p>}</div>;
  }
  if (["timeseries", "breakdown", "ranking"].includes(widget.type)) return <EChartsBase option={chartOption(value as Chart)} />;
  if (widget.type === "quality") { const q = value as Quality; return <p>{q.total_issues} hallazgos · {q.error_count} errores · {q.warning_count} advertencias</p>; }
  if (widget.type === "insights") {
    const insights = (value as { insights?: Array<{ id: string; template_key: string; params: Record<string, unknown> }> }).insights ?? [];
    return <ul className="space-y-2">{insights.map((item) => <li key={item.id} className="rounded-xl bg-amber-50 p-3">{labels[item.template_key] ?? item.template_key}: {JSON.stringify(item.params)}</li>)}</ul>;
  }
  return <ErrorState />;
}

export function DashboardRenderer({ dashboard }: { dashboard: DashboardResponse }) {
  const terminology = dashboard.spec.terminology ?? {};
  return <div className="space-y-8">{dashboard.spec.sections.map((section) => <section key={section.id}><h2 className="mb-4 text-2xl font-semibold">{title(section.title_key, terminology)}</h2><div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-12">{section.widgets.map((widget) => <article key={widget.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-3" style={{ gridColumn: `span ${widget.layout.span}` }}><h3 className="mb-4 font-semibold">{title(widget.title_key, terminology)}</h3><WidgetView widget={widget} value={dashboard.data[widget.id]} /></article>)}</div></section>)}</div>;
}

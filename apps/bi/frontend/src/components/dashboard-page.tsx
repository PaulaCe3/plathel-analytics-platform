"use client";

import { useEffect, useState } from "react";
import { DashboardRenderer } from "./dashboard-renderer";
import { DashboardResponse, FilterClause, getDashboard, getFilterOptions } from "@/lib/api/dashboard";

export function DashboardPage({ datasetId }: { datasetId: string }) {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [filters, setFilters] = useState<FilterClause[]>([]);
  const [searchOptions, setSearchOptions] = useState<Record<string, string[]>>({});
  const [status, setStatus] = useState("Cargando dashboard…");
  useEffect(() => { getDashboard(datasetId, { filters, comparison: { mode: "previous_period" }, grain: "auto" }).then(setDashboard).catch((error) => setStatus(error instanceof Error ? error.message : "No se pudo cargar el dashboard.")); }, [datasetId, filters]);
  if (!dashboard) return <p className="rounded-2xl bg-white p-6">{status}</p>;
  function replaceFilter(field: string, next?: FilterClause) { setFilters((current) => [...current.filter((item) => item.field !== field), ...(next ? [next] : [])]); }
  function datePart(field: string, index: number, value: string, minimum?: string | null, maximum?: string | null) {
    const existing = filters.find((item) => item.field === field && item.op === "between");
    const values = existing?.values.map(String) ?? [minimum ?? value, maximum ?? value]; values[index] = value;
    if (values[0] && values[1]) replaceFilter(field, { field, op: "between", values });
  }
  return <div className="space-y-6"><header><p className="text-sm text-slate-500">{dashboard.filtered_row_count} de {dashboard.row_count} filas</p><h1 className="text-3xl font-bold">Dashboard</h1></header><div className="flex flex-wrap gap-3 rounded-2xl bg-white p-4">{dashboard.spec.filters.map((filter) => filter.type === "date_range" ? <div key={filter.id} className="flex gap-2"><input aria-label={`${filter.field} desde`} type="date" min={filter.minimum ?? undefined} max={filter.maximum ?? undefined} onChange={(event) => datePart(filter.field, 0, event.target.value, filter.minimum, filter.maximum)} className="rounded-xl border p-2"/><input aria-label={`${filter.field} hasta`} type="date" min={filter.minimum ?? undefined} max={filter.maximum ?? undefined} onChange={(event) => datePart(filter.field, 1, event.target.value, filter.minimum, filter.maximum)} className="rounded-xl border p-2"/></div> : filter.type === "search" ? <div key={filter.id}><input list={`options-${filter.id}`} placeholder={`Buscar ${filter.field}`} className="rounded-xl border p-2" onChange={(event) => { const value = event.target.value; replaceFilter(filter.field, value ? { field: filter.field, op: "contains", values: [value] } : undefined); if (value.length >= 2) getFilterOptions(datasetId, filter.field, value).then((result) => setSearchOptions((current) => ({ ...current, [filter.field]: result.options.map((item) => item.value) }))); }}/><datalist id={`options-${filter.id}`}>{(searchOptions[filter.field] ?? []).map((value) => <option key={value} value={value}/>)}</datalist></div> : <select key={filter.id} aria-label={filter.label_key} className="rounded-xl border p-2" onChange={(event) => replaceFilter(filter.field, event.target.value ? { field: filter.field, op: "in", values: [event.target.value] } : undefined)}><option value="">Todos · {filter.field}</option>{filter.options?.map((option) => <option key={option.value} value={option.value}>{option.value} ({option.count})</option>)}</select>)}</div><DashboardRenderer dashboard={dashboard} />{dashboard.spec.unavailable_metrics.length > 0 && <details className="rounded-2xl bg-white p-5"><summary>Métricas no disponibles ({dashboard.spec.unavailable_metrics.length})</summary><ul>{dashboard.spec.unavailable_metrics.map((metric) => <li key={metric.metric_id}>{metric.label_key ?? metric.metric_id}: {metric.missing_fields.join(", ") || (metric.reason_key === "metric.requires_cost_basis_total" ? "Requiere costo total explícito (basis: total)" : metric.reason_key === "metric.requires_discount_kind_amount" ? "Requiere descuento como importe explícito (kind: amount)" : "contexto no compatible")}</li>)}</ul></details>}</div>;
}

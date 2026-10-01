import type { EChartsOption } from "echarts";
import type { components } from "@/types/api.generated";

type ChartResult = components["schemas"]["ChartResult"];

export function chartOption(result: ChartResult, label = "Valor"): EChartsOption {
  const points = result.series?.[0]?.points ?? [];
  const categories = points.map((point) => String(point[0] ?? ""));
  const values = points.map((point) => Number(point[1] ?? 0));
  const horizontal = result.chart !== "timeseries";
  return {
    animation: false,
    color: ["#596B52", "#3F4D3B", "#75866C", "#98A590", "#BEC6B8"],
    textStyle: { color: "#404245", fontFamily: "Arial, Helvetica, sans-serif" },
    legend: { data: [label], top: 0 },
    tooltip: { trigger: "axis" },
    grid: { left: 48, right: 24, top: 40, bottom: 48, containLabel: true },
    xAxis: horizontal ? { type: "value" } : { type: "category", data: categories },
    yAxis: horizontal ? { type: "category", data: categories } : { type: "value" },
    series: [{ name: label, type: result.chart === "timeseries" ? "line" : "bar", data: values, smooth: result.chart === "timeseries", areaStyle: result.chart === "timeseries" ? { color: "#BEC6B8", opacity: 0.3 } : undefined }],
  };
}

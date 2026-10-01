import type { EChartsOption } from "echarts";
import type { components } from "@/types/api.generated";

type ChartResult = components["schemas"]["ChartResult"];

export function chartOption(result: ChartResult, label = "Valor", selected: string[] = []): EChartsOption {
  const points = result.series?.[0]?.points ?? [];
  const categories = points.map((point) => String(point[0] ?? ""));
  const values = points.map((point) => Number(point[1] ?? 0));
  const horizontal = result.chart !== "timeseries";
  return {
    animation: false,
    color: ["#596B52", "#3F4D3B", "#75866C", "#98A590", "#BEC6B8"],
    textStyle: { color: "#404245", fontFamily: "Inter, Arial, sans-serif" },
    legend: { show: false },
    tooltip: { trigger: "axis", confine: true, backgroundColor: "#EEEFEF", borderColor: "#D1D3D3", textStyle: {color:"#141616"} },
    grid: { left: 48, right: 24, top: 16, bottom: 48, containLabel: true },
    xAxis: horizontal ? { type: "value", splitLine:{lineStyle:{color:"#D1D3D3",opacity:0.45}},axisLabel:{hideOverlap:true} } : { type: "category", data: categories, axisLabel: { hideOverlap: true, formatter: (value: string) => /^\d{4}-\d{2}(-\d{2})?$/.test(value)?new Intl.DateTimeFormat("es-AR", {month:"short",year:"numeric",...(result.grain==="day"?{day:"numeric" as const}:{}),timeZone:"UTC"}).format(new Date(`${value.slice(0,10)}${value.length===7?"-01":""}T00:00:00Z`)):value.replace(/^(\d{4})Q([1-4])$/, "$2.º trim. $1") } },
    yAxis: horizontal ? { type: "category", data: categories } : { type: "value", splitLine:{lineStyle:{color:"#D1D3D3",opacity:0.45}} },
    series: [{ name: label, type: result.chart === "timeseries" ? "line" : "bar", barMaxWidth: 36, emphasis: {itemStyle:{borderWidth:2,borderColor:"#3F4D3B"}}, data: selected.length?values.map((value,index)=>({value,itemStyle:{color:selected.includes(categories[index])?"#3F4D3B":"#98A590",borderColor:selected.includes(categories[index])?"#141616":undefined,borderWidth:selected.includes(categories[index])?2:0}})):values, smooth: false, areaStyle: result.chart === "timeseries" ? { color: "#BEC6B8", opacity: 0.3 } : undefined }],
  };
}

import type { EChartsOption } from "echarts";
import type { components } from "@/types/api.generated";

type ChartResult = components["schemas"]["ChartResult"];

export function chartOption(result: ChartResult, label = "Valor", selected: string[] = []): EChartsOption {
  const points = result.series?.[0]?.points ?? [];
  const categories = points.map((point) => String(point[0] ?? ""));
  const values = points.map((point) => Number(point[1] ?? 0));
  const horizontal = result.chart !== "timeseries";
  const number = (value: unknown) => typeof value === "number" ? new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 }).format(value) : String(value ?? "");
  return {
    animation: false,
    color: ["#4F5948", "#404245", "#5F5D5C", "#B9BABA", "#D1D3D3"],
    textStyle: { color: "#404245", fontFamily: "Inter, Arial, sans-serif" },
    legend: { show: false },
    tooltip: { trigger: "axis", confine: true, backgroundColor: "#EEEFEF", borderColor: "#D1D3D3", textStyle: {color:"#141616"}, valueFormatter:number },
    grid: { left: 48, right: 24, top: 16, bottom: 48, containLabel: true },
    xAxis: horizontal ? { type: "value", splitLine:{lineStyle:{color:"#D1D3D3",opacity:0.34}},axisLabel:{hideOverlap:true,color:"#5F5D5C",formatter:number} } : { type: "category", data: categories, axisLine:{lineStyle:{color:"#B9BABA"}},axisTick:{show:false},axisLabel: { color:"#5F5D5C",hideOverlap: true, formatter: (value: string) => /^\d{4}-\d{2}(-\d{2})?$/.test(value)?new Intl.DateTimeFormat("es-AR", {month:"short",year:"numeric",...(result.grain==="day"?{day:"numeric" as const}:{}),timeZone:"UTC"}).format(new Date(`${value.slice(0,10)}${value.length===7?"-01":""}T00:00:00Z`)):value.replace(/^(\d{4})Q([1-4])$/, "$2.º trim. $1") } },
    yAxis: horizontal ? { type: "category", data: categories,axisLine:{show:false},axisTick:{show:false},axisLabel:{color:"#5F5D5C"} } : { type: "value", splitLine:{lineStyle:{color:"#D1D3D3",opacity:0.34}},axisLabel:{color:"#5F5D5C",formatter:number} },
    series: [{ name: label, type: result.chart === "timeseries" ? "line" : "bar", barMaxWidth: 34, symbol:"circle",symbolSize:result.chart === "timeseries"?5:undefined,itemStyle:{color:result.chart === "timeseries"?"#4F5948":"#404245"},lineStyle:result.chart === "timeseries"?{color:"#4F5948",width:2}:undefined,emphasis: {itemStyle:{color:"#4F5948",borderWidth:2,borderColor:"#141616"}}, data: selected.length?values.map((value,index)=>({value,itemStyle:{color:selected.includes(categories[index])?"#4F5948":"#B9BABA",borderColor:selected.includes(categories[index])?"#141616":undefined,borderWidth:selected.includes(categories[index])?2:0}})):values, smooth: false, areaStyle: result.chart === "timeseries" ? { color: "#D1D3D3", opacity: 0.16 } : undefined }],
  };
}

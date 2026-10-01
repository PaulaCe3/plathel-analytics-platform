"use client";

import { useEffect, useRef } from "react";
import type { EChartsOption } from "echarts";

export type ChartInteraction = {dataIndex: number; name: string};
export function EChartsBase({ option, label, onSelect }: { option: EChartsOption; label: string; onSelect?: (event: ChartInteraction) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let disposed = false;
    let observer: ResizeObserver | undefined;
    let chart: import("echarts").ECharts | undefined;
    import("echarts").then((echarts) => {
      if (!ref.current || disposed) return;
      chart = echarts.init(ref.current); chart.setOption({ ...option, aria: { enabled: true, description: label, decal: { show: true } } });
      if(onSelect) chart.on("click", (event: {dataIndex?: number; name?: string}) => {if(typeof event.dataIndex === "number") onSelect({dataIndex:event.dataIndex,name:event.name ?? ""});});
      observer = new ResizeObserver(() => chart?.resize()); observer.observe(ref.current);
    });
    return () => { disposed = true; observer?.disconnect(); chart?.dispose(); };
  }, [option, label, onSelect]);
  return <div ref={ref} className="pl-chart-canvas" role="img" aria-label={label} />;
}

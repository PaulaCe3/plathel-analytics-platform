"use client";

import { useEffect, useRef } from "react";
import type { EChartsOption } from "echarts";

export function EChartsBase({ option, label }: { option: EChartsOption; label: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let disposed = false;
    let observer: ResizeObserver | undefined;
    let chart: import("echarts").ECharts | undefined;
    import("echarts").then((echarts) => {
      if (!ref.current || disposed) return;
      chart = echarts.init(ref.current); chart.setOption({ ...option, aria: { enabled: true, description: label, decal: { show: true } } });
      observer = new ResizeObserver(() => chart?.resize()); observer.observe(ref.current);
    });
    return () => { disposed = true; observer?.disconnect(); chart?.dispose(); };
  }, [option, label]);
  return <div ref={ref} className="h-80 w-full" role="img" aria-label={label} />;
}

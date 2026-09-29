"use client";

import { useEffect, useRef } from "react";
import type { EChartsOption } from "echarts";

export function EChartsBase({ option }: { option: EChartsOption }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let disposed = false;
    let chart: import("echarts").ECharts | undefined;
    import("echarts").then((echarts) => {
      if (!ref.current || disposed) return;
      chart = echarts.init(ref.current); chart.setOption(option);
    });
    return () => { disposed = true; chart?.dispose(); };
  }, [option]);
  return <div ref={ref} className="h-80 w-full" role="img" aria-label="Visualización de datos" />;
}

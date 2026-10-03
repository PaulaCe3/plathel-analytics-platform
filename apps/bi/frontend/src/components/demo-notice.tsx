"use client";
import { t } from "@/lib/i18n";
import { useEffect, useState } from "react";
import { getDataset } from "@/lib/api/datasets";

export function DemoNotice({ datasetId }: { datasetId: string }) {
  const [demo, setDemo] = useState("");
  useEffect(() => { let active = true; getDataset(datasetId).then((dataset) => { if (active) setDemo(dataset.demo_id ?? ""); }).catch(() => {}); return () => { active = false; }; }, [datasetId]);
  if (!demo) return null;
  const labels:Record<string,string>={retail_demo:"Retail / E-commerce",retail_forecast_demo:"Retail / E-commerce",services_demo:"Servicios",hospitality_demo:"Hotelería"};
  return <aside aria-label={t("demo-notice.text1")} className="pl-demo-notice">{labels[demo]??"Demostración"}</aside>;
}

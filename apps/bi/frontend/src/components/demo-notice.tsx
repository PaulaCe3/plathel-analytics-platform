"use client";
import { t } from "@/lib/i18n";
import { useEffect, useState } from "react";
import { getDataset } from "@/lib/api/datasets";

export function DemoNotice({ datasetId }: { datasetId: string }) {
  const [isDemo, setIsDemo] = useState(false);
  useEffect(() => { let active = true; getDataset(datasetId).then((dataset) => { if (active) setIsDemo(Boolean(dataset.demo_id)); }).catch(() => {}); return () => { active = false; }; }, [datasetId]);
  if (!isDemo) return null;
  return <aside aria-label={t("demo-notice.text1")} className="pl-demo-notice">DEMO</aside>;
}

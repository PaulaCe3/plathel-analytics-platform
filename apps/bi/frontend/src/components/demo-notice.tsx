"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getDataset } from "@/lib/api/datasets";

export function DemoNotice({ datasetId }: { datasetId: string }) {
  const [isDemo, setIsDemo] = useState(false);
  useEffect(() => { let active = true; getDataset(datasetId).then((dataset) => { if (active) setIsDemo(Boolean(dataset.demo_id)); }).catch(() => {}); return () => { active = false; }; }, [datasetId]);
  if (!isDemo) return null;
  return <aside className="rounded-xl bg-blue-50 p-4 text-sm text-blue-950">Modo demo · Datos sintéticos. <Link className="underline" href={`/bi/${datasetId}/mapping`}>Revisar mapping</Link></aside>;
}

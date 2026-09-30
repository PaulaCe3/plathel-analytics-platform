"use client";
import { t } from "@/lib/i18n";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createDemo, DemoSummary, getDemos } from "@/lib/api/demos";

export function DemoSelector() {
  const router = useRouter();
  const [demos, setDemos] = useState<DemoSummary[]>([]);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { getDemos().then(setDemos).catch((error) => setStatus(error instanceof Error ? error.message : t("demo-selector.text1"))); }, []);
  async function openDemo(id: string) {
    setBusy(true); setStatus(t("demo-selector.text2"));
    try {
      const dataset = await createDemo(id);
      router.push(`/bi/${dataset.dataset_id}/${dataset.stage === "mapped" ? "review" : "mapping"}`);
    } catch (error) { setStatus(error instanceof Error ? error.message : t("demo-selector.text3")); setBusy(false); }
  }
  return <section className="rounded-2xl border border-blue-200 bg-blue-50 p-6">
    <h2 className="text-xl font-semibold">{t("demo-selector.action1")}</h2>
    <p className="mt-2 text-sm text-slate-700">{t("demo-selector.text4")}</p>
    <div className="mt-4 flex flex-wrap gap-3">{demos.map((demo) => <button key={demo.id} disabled={busy} title={demo.description} onClick={() => openDemo(demo.id)} className="rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white disabled:opacity-40">{demo.name}</button>)}</div>
    <p role="status" className="mt-3 text-sm text-slate-700">{status}</p>
  </section>;
}

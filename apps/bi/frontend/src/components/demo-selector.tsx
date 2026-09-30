"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createDemo, DemoSummary, getDemos } from "@/lib/api/demos";

export function DemoSelector() {
  const router = useRouter();
  const [demos, setDemos] = useState<DemoSummary[]>([]);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { getDemos().then(setDemos).catch((error) => setStatus(error instanceof Error ? error.message : "No se pudieron cargar las demos.")); }, []);
  async function openDemo(id: string) {
    setBusy(true); setStatus("Preparando la demo…");
    try {
      const dataset = await createDemo(id);
      router.push(`/bi/${dataset.dataset_id}/${dataset.stage === "mapped" ? "review" : "mapping"}`);
    } catch (error) { setStatus(error instanceof Error ? error.message : "No se pudo crear la demo."); setBusy(false); }
  }
  return <section className="rounded-2xl border border-blue-200 bg-blue-50 p-6">
    <h2 className="text-xl font-semibold">Probar demo</h2>
    <p className="mt-2 text-sm text-slate-700">Explorá datos sintéticos. Revisá el mapping y confirmá la limpieza para ver el dashboard.</p>
    <div className="mt-4 flex flex-wrap gap-3">{demos.map((demo) => <button key={demo.id} disabled={busy} title={demo.description} onClick={() => openDemo(demo.id)} className="rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white disabled:opacity-40">{demo.name}</button>)}</div>
    <p role="status" className="mt-3 text-sm text-slate-700">{status}</p>
  </section>;
}

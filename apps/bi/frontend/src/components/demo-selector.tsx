"use client";
import { HomeIcon } from "@/components/home-sections";
import { t } from "@/lib/i18n";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createDemo, DemoSummary, getDemos } from "@/lib/api/demos";

export function DemoSelector() {
  const router = useRouter();
  const [demos, setDemos] = useState<DemoSummary[]>([]);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [active, setActive] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => { getDemos().then(setDemos).catch((error) => setStatus(error instanceof Error ? error.message : t("demo-selector.text1"))); }, []);
  async function openDemo(id: string) {
    setActive(id); setFailed(false); setBusy(true); setStatus(t("demo-selector.text2"));
    try {
      const dataset = await createDemo(id);
      router.push(`/bi/${dataset.dataset_id}/results`);
    } catch (error) { setStatus(error instanceof Error ? error.message : t("demo-selector.text3")); setBusy(false); setFailed(true); }
  }
  const kinds = ["retail", "services", "hospitality"];
  return <section id="demos" tabIndex={-1} className="home-section" aria-labelledby="demos-title" aria-busy={busy}>
    <h2 id="demos-title">Elegí una demostración</h2>
    <div className="home-demo-grid">{kinds.map(kind=>{const demo=demos.find(d=>d.id === (kind==="retail"?"retail_forecast_demo":`${kind}_demo`));return <article key={kind} className="home-demo-card"><HomeIcon kind={kind}/><h3>{t(`home.${kind}`)}</h3><p>{t(`home.${kind}Desc`)}</p><button disabled={busy || !demo} onClick={()=>demo && openDemo(demo.id)}>{active === demo?.id && busy ? "Preparando la demostración…" : "Explorar demo"} <span aria-hidden="true">→</span></button></article>;})}</div>
    {busy && <div className="home-demo-progress" role="status" aria-live="polite"><strong>Preparando la demostración</strong><ul><li>✓ Datos preparados</li><li>✓ Análisis generado</li><li>○ Preparando resultados</li></ul></div>}
    <p role={failed ? "alert" : "status"} className={`home-feedback ${failed ? "home-error" : ""}`}>{status}</p>
  </section>;
}

"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getDataset, deleteDataset } from "@/lib/api/datasets";
import { t } from "@/lib/i18n";
export function SessionControls({ datasetId }: { datasetId: string }) {
  const router = useRouter();
  const [expiry, setExpiry] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const expired = () => router.replace("/bi?expired=1");
    window.addEventListener("dataset-session-ended", expired);
    getDataset(datasetId).then((dataset) => setExpiry(new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "short" }).format(new Date(dataset.expires_at)))).catch((error) => setStatus(error.message));
    return () => window.removeEventListener("dataset-session-ended", expired);
  }, [datasetId, router]);
  async function finish() {
    setBusy(true); setStatus(t("session.deleting"));
    try { await deleteDataset(datasetId); router.replace("/bi?deleted=1"); }
    catch (error) { setStatus(error instanceof Error ? error.message : t("request.failed")); setBusy(false); }
  }
  return <aside aria-label={t("session-controls.text1")} className="mx-auto max-w-6xl px-6 pt-6"><p className="text-sm">{t("session.privacy")} {expiry && `Vencimiento por inactividad: ${expiry}.`}</p><button disabled={busy} onClick={finish} className="mt-3 rounded-lg border border-slate-500 px-4 py-2">{t("session.delete")}</button><p role="status">{status}</p></aside>;
}

"use client";
import { Button, Toast } from "@/components/ui/primitives";
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
    getDataset(datasetId).then((dataset) => setExpiry(new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "short" }).format(new Date(dataset.expires_at)))).catch(() => setStatus(t("product.sessionError")));
    return () => window.removeEventListener("dataset-session-ended", expired);
  }, [datasetId, router]);
  async function finish() {
    setBusy(true); setStatus(t("session.deleting"));
    try { await deleteDataset(datasetId); router.replace("/bi?deleted=1"); }
    catch { setStatus(t("product.sessionError")); setBusy(false); }
  }
  return <div className="pl-session-controls"><details className="pl-session-menu"><summary>Opciones</summary><div className="pl-session-menu-content"><a href={`/bi/${datasetId}/mapping`}>Revisar datos</a><details><summary>{t("product.privacy")}</summary><div><p>{t("session.privacy")}</p>{expiry && <p>{t("product.expiry")}: {expiry}.</p>}</div></details><Button variant="danger" busy={busy} onClick={finish}>{t("session.delete")}</Button><Toast tone="error">{busy ? null : status}</Toast></div></details></div>;
}

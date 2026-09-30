import { t } from "@/lib/i18n";
import { ColumnMapper } from "@/components/column-mapper";

export default async function MappingPage({ params }: { params: Promise<{ datasetId: string }> }) {
  const { datasetId } = await params;
  return <main className="min-h-screen px-6 py-12"><section className="mx-auto max-w-6xl"><p className="text-sm font-semibold uppercase tracking-wide text-slate-600">{t("app.bi.datasetId.mapping.page.text1")}</p><h1 className="mt-2 text-4xl font-semibold tracking-tight">{t("app.bi.datasetId.mapping.page.text2")}</h1><p className="mb-8 mt-3 text-slate-600">{t("app.bi.datasetId.mapping.page.text3")}</p><ColumnMapper datasetId={datasetId} /></section></main>;
}

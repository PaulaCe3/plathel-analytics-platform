import { t } from "@/lib/i18n";
import { DatasetReview } from "@/components/dataset-review";

export default async function ReviewPage({ params }: { params: Promise<{ datasetId: string }> }) {
  const { datasetId } = await params;
  return <main className="min-h-screen px-6 py-12"><section className="mx-auto max-w-5xl"><p className="text-sm font-semibold uppercase tracking-wide text-slate-600">{t("app.bi.datasetId.review.page.text1")}</p><h1 className="mt-2 text-4xl font-semibold tracking-tight">{t("app.bi.datasetId.review.page.text2")}</h1><p className="mb-8 mt-3 text-slate-600">{t("app.bi.datasetId.review.page.text3")}</p><DatasetReview datasetId={datasetId} /></section></main>;
}

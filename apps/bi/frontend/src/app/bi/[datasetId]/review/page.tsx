import { DatasetReview } from "@/components/dataset-review";

export default async function ReviewPage({ params }: { params: Promise<{ datasetId: string }> }) {
  const { datasetId } = await params;
  return <main className="min-h-screen px-6 py-12"><section className="mx-auto max-w-5xl"><p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Fase 3 · Revisión</p><h1 className="mt-2 text-4xl font-semibold tracking-tight">Validación, calidad y limpieza</h1><p className="mb-8 mt-3 text-slate-600">Los hallazgos no modifican tus datos. Solo se aplicarán las acciones que confirmes.</p><DatasetReview datasetId={datasetId} /></section></main>;
}

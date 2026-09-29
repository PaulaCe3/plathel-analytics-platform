import { ColumnMapper } from "@/components/column-mapper";

export default async function MappingPage({ params }: { params: Promise<{ datasetId: string }> }) {
  const { datasetId } = await params;
  return <main className="min-h-screen px-6 py-12"><section className="mx-auto max-w-6xl"><p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Fase 2 · Column mapping</p><h1 className="mt-2 text-4xl font-semibold tracking-tight">Asigná significado a tus columnas</h1><p className="mb-8 mt-3 text-slate-600">Confirmá las sugerencias automáticas o elegí otra disposición.</p><ColumnMapper datasetId={datasetId} /></section></main>;
}

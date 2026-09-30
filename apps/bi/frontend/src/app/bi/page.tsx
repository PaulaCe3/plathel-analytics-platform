import { DemoSelector } from "@/components/demo-selector";
import { DatasetIngestion } from "@/components/dataset-ingestion";

export default function BiHome() {
  return (
    <main className="min-h-screen px-6 py-12">
      <section className="mx-auto w-full max-w-6xl">
        <div className="mb-8 inline-flex rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-600">
          Análisis de datos
        </div>
        <h1 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
          BI Multi-Industria
        </h1>
        <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">
          Cargá un archivo y revisá su estructura antes del análisis.
        </p>
        <div className="mt-10">
          <div className="space-y-8"><DemoSelector /><DatasetIngestion /></div>
        </div>
      </section>
    </main>
  );
}

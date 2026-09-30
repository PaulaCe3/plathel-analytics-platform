import { DemoSelector } from "@/components/demo-selector";
import { DatasetIngestion } from "@/components/dataset-ingestion";

import { t } from "@/lib/i18n";

export default async function BiHome({ searchParams }: { searchParams: Promise<{ expired?: string; deleted?: string }> }) {
  const notice = await searchParams;
  return (
    <main className="min-h-screen px-6 py-12">
      <section className="mx-auto w-full max-w-6xl">
        <div className="mb-8 inline-flex rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-600">{t("app.bi.page.text1")}</div>
        <h1 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">{t("app.bi.page.text2")}</h1>
        <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">{t("app.bi.page.text3")}</p>
        <p className="mt-4 text-sm">{t("session.privacy")}</p>
        {(notice.expired || notice.deleted) && <p role="status" className="mt-4 rounded-xl bg-blue-50 p-4">{t(notice.expired ? "session.expired" : "session.deleted")}</p>}
        <div className="mt-10">
          <div className="space-y-8"><DemoSelector /><DatasetIngestion /></div>
        </div>
      </section>
    </main>
  );
}

import { DashboardPage } from "@/components/dashboard-page";

export default async function Page({ params }: { params: Promise<{ datasetId: string }> }) {
  const { datasetId } = await params;
  return <main className="min-h-screen bg-slate-100 p-6 md:p-10"><DashboardPage datasetId={datasetId} /></main>;
}

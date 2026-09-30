import { DashboardPage } from "@/components/dashboard-page";

export default async function Page({ params }: { params: Promise<{ datasetId: string }> }) {
  const { datasetId } = await params;
  return <main className="pl-main"><DashboardPage datasetId={datasetId} /></main>;
}

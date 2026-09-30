import { SessionControls } from "@/components/session-controls";
export default async function SessionLayout({ children, params }: { children: React.ReactNode; params: Promise<{ datasetId: string }> }) {
  const { datasetId } = await params;
  return <><SessionControls datasetId={datasetId} />{children}</>;
}

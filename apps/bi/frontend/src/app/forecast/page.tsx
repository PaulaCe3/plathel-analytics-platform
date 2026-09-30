import { ForecastWorkspace } from "@/forecast/workspace";
export default async function ForecastPage({searchParams}:{searchParams:Promise<{dataset?:string}>}) {
 const {dataset}=await searchParams;
 return <ForecastWorkspace datasetId={dataset}/>;
}

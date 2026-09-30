import { DemoSelector } from "@/components/demo-selector";
import { DatasetIngestion } from "@/components/dataset-ingestion";
import { HomeHeader, HomeHero, HomeExplanation } from "@/components/home-sections";
import { HomeNotice } from "@/components/home-notice";
import "./home.css";
export default async function BiHome({searchParams}:{searchParams:Promise<{expired?:string;deleted?:string}>}) {
 const notice=await searchParams;
 return <div className="bi-home"><div className="home-shell"><HomeHeader/><main><HomeHero/><HomeNotice deleted={notice.deleted === "1"} expired={!!notice.expired}/><DatasetIngestion/><DemoSelector/><HomeExplanation/></main></div></div>;
}

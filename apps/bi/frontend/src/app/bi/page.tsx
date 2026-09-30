import {DemoSelector} from "@/components/demo-selector";
import {DatasetIngestion} from "@/components/dataset-ingestion";
import {ProductHeader,Stepper} from "@/components/product-navigation";
import {HomeNotice} from "@/components/home-notice";
import "./home.css";
export default async function BiHome({searchParams}:{searchParams:Promise<{expired?:string;deleted?:string}>}){const notice=await searchParams;return <div className="bi-home"><div className="home-shell"><ProductHeader/><Stepper/><main className="pl-data-home"><div className="pl-page-heading"><p className="home-eyebrow">01 / DATOS</p><h1>Subí tus datos</h1><p>Cargá tu archivo Excel o CSV. Te vamos guiando con el resto.</p></div><HomeNotice deleted={notice.deleted==="1"} expired={!!notice.expired}/><DatasetIngestion/><details className="pl-details pl-demo-choice"><summary>Probar con datos de ejemplo</summary><DemoSelector/></details></main></div></div>;}

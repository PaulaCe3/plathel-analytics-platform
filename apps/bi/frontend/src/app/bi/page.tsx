import {DemoSelector} from "@/components/demo-selector";
import {ProductHeader,Stepper} from "@/components/product-navigation";
import {HomeNotice} from "@/components/home-notice";
import "./home.css";
export default async function BiHome({searchParams}:{searchParams:Promise<{expired?:string;deleted?:string}>}){const notice=await searchParams;return <div className="bi-home"><div className="home-shell"><ProductHeader/><Stepper/><main className="pl-data-home"><div className="pl-page-heading"><h1>Explorá PLATHEL</h1><p>Elegí un ejemplo y descubrí cómo PLATHEL transforma datos en resultados, predicciones y una vista interactiva del negocio.</p></div><HomeNotice deleted={notice.deleted==="1"} expired={!!notice.expired}/><DemoSelector/><p className="home-demo-note">Esta es una demostración simplificada de PLATHEL con datos de ejemplo. Cada implementación real se adapta a los datos, métricas, análisis, filtros y necesidades específicas de cada empresa.</p></main></div></div>;}

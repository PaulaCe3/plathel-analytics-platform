import {t} from "@/lib/i18n";
import {ColumnMapper} from "@/components/column-mapper";
export default async function Page({params}:{params:Promise<{datasetId:string}>}){const {datasetId}=await params;return <main className="pl-main"><div className="pl-page-heading"><h1>{t("product.mappingTitle")}</h1><p>{t("product.mappingIntro")}</p></div><ColumnMapper datasetId={datasetId}/></main>;}

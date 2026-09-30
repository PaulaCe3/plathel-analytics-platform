import {t} from "@/lib/i18n";
import {DatasetReview} from "@/components/dataset-review";
export default async function Page({params}:{params:Promise<{datasetId:string}>}){const {datasetId}=await params;return <main className="pl-main"><div className="pl-page-heading"><h1>{t("product.reviewTitle")}</h1><p>{t("product.reviewIntro")}</p></div><DatasetReview datasetId={datasetId}/></main>;}

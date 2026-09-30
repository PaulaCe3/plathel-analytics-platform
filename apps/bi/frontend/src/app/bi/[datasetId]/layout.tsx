import { SessionControls } from "@/components/session-controls";
import { ProductHeader, Stepper } from "@/components/product-navigation";
export default async function SessionLayout({children,params}:{children:React.ReactNode;params:Promise<{datasetId:string}>}){const {datasetId}=await params;return <div className="pl-session"><div className="pl-shell"><ProductHeader><SessionControls datasetId={datasetId}/></ProductHeader><Stepper/>{children}</div></div>;}

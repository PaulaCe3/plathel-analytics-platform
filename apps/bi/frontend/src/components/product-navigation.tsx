"use client";
import {usePathname} from "next/navigation";
import {ProductHeader as SharedHeader,JourneyNavigation} from "@plathel/ui/product-header";
export function ProductHeader({children}:{children?:React.ReactNode}){return <SharedHeader>{children}</SharedHeader>;}
export function Stepper(){const path=usePathname();const datasetId=path.match(/^\/bi\/([^/]+)\//)?.[1];return <JourneyNavigation current={path.endsWith("/dashboard")?3:path.endsWith("/results")||path.startsWith("/forecast")?2:1} datasetId={datasetId}/>;}

"use client";
import { usePathname } from "next/navigation";
import { t } from "@/lib/i18n";
import { ProductHeader as SharedHeader } from "@plathel/ui/product-header";
export function ProductHeader({home=false,children}:{home?:boolean;children?:React.ReactNode}){const path=usePathname();const dataset=path.match(/^\/bi\/([^/]+)\//)?.[1];return <SharedHeader area="analysis" forecastHref={dataset ? `/forecast?dataset=${encodeURIComponent(dataset)}` : "/forecast"}>{home ? <a href="#how-it-works">{t("home.how")}</a> : children}</SharedHeader>;}
export function Stepper(){const path=usePathname();const current=path.endsWith("/mapping")?2:path.endsWith("/review")?3:path.endsWith("/dashboard")?4:1;return <nav aria-label={t("product.stepper")} className="pl-stepper"><ol>{[1,2,3,4].map(n=><li key={n} aria-current={n === current ? "step" : undefined} data-state={n < current ? "complete" : n === current ? "current" : "future"}><span aria-hidden="true">{n<current ? "✓" : `0${n}`}</span><span>{t(`product.step${n}`)}</span><span className="sr-only">{t(n<current ? "product.completed" : n === current ? "product.current" : "product.future")}</span></li>)}</ol></nav>;}

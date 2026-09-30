"use client";
import type { ReactNode } from "react";

export function ProductHeader({ area, forecastHref="/forecast", children }: {area:"analysis"|"forecast";forecastHref?:string;children?:ReactNode}) {
 return <header className="pl-header"><a href="/bi" className="pl-wordmark">PLATHEL<span>DATA · AI · AUTOMATION</span></a><nav className="pl-product-nav" aria-label="Áreas de PLATHEL"><a href="/bi" aria-current={area==="analysis"?"page":undefined}>Análisis</a><a href={forecastHref} aria-current={area==="forecast"?"page":undefined}>Predicciones</a></nav><div className="pl-header-actions">{children}</div></header>;
}

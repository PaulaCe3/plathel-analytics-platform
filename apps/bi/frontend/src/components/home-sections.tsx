import { ProductHeader } from "@/components/product-navigation";
import { t } from "@/lib/i18n";
import type { ReactNode } from "react";
export function HomeIcon({ kind = "chart" }: { kind?: string }) {
 const paths: Record<string,string> = { upload: "M12 16V3m-5 5 5-5 5 5M4 15v5h16v-5", chart: "M4 20h16M7 16v-5m5 5V5m5 11v-8", filter: "M4 6h16M7 12h10m-7 6h4", insight: "m13 3-7 11h6l-1 7 7-11h-6l1-7", export: "M12 3v13m-5-5 5 5 5-5M4 17v4h16v-4", shield: "m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3m-4 9 3 3 5-6", retail: "M4 10h16v11H4V10m-1 0 2-7h14l2 7M9 21v-7h6v7", services: "M4 7h16v13H4V7m4 0V3h8v4M4 12h16", hospitality: "M4 21V3h16v18M8 7h1m6 0h1M8 11h1m6 0h1M10 21v-6h4v6" };
 return <svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d={paths[kind] ?? paths.chart}/></svg>;
}
export function HomeHeader() { return <ProductHeader home/>; }
export function HomeHero() { return <section className="home-hero"><p className="home-eyebrow">{t("product.businessIntelligence")}</p><h1>{t("home.hero")}</h1><p className="home-intro">{t("home.intro")}</p><div className="home-actions"><a className="home-primary" href="#upload">{t("home.analyze")} <span aria-hidden="true">↗</span></a><a className="home-secondary" href="#demos">{t("home.demo")} <span aria-hidden="true">→</span></a></div><ul className="home-trust">{[1,2,3].map(n=><li key={n}><span aria-hidden="true">✓</span> {t(`home.trust${n}`)}</li>)}</ul></section>;
}
function Section({id,title,children}:{id?:string;title:string;children:ReactNode}) {return <section id={id} className="home-section" tabIndex={id ? -1 : undefined}><h2>{t(title)}</h2>{children}</section>;}
export function HomeExplanation() {
 return <><Section id="how-it-works" title="home.steps"><ol className="home-steps">{[1,2,3,4].map(n=><li key={n}><span className="home-step-number">0{n}</span><h3>{t(`home.step${n}`)}</h3><p>{t(`home.step${n}Desc`)}</p></li>)}</ol></Section><Section title="home.benefits"><div className="home-benefits">{["chart","filter","insight","export"].map((kind,i)=><article key={kind}><HomeIcon kind={kind}/><h3>{t(`home.benefit${i+1}`)}</h3><p>{t(`home.benefit${i+1}Desc`)}</p></article>)}</div></Section><Section title="home.industries"><ul className="home-industries">{["retail","services","hospitality","custom"].map(key=><li key={key}>{t(`home.${key}`)}</li>)}</ul><p>{t("home.industryIntro")}</p></Section><aside className="home-privacy" aria-labelledby="privacy-title"><HomeIcon kind="shield"/><div><h2 id="privacy-title">{t("home.privacy")}</h2><p>{t("home.privacyIntro")}</p></div></aside></>;
}

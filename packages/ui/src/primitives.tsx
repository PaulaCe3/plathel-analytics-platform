"use client";
import { useEffect, useId, useRef, type ReactNode, type ComponentProps } from "react";
const uiMessages:Record<string,string>={"widget.empty":"No hay datos para mostrar.","widget.error":"No pudimos mostrar este bloque. Intentá actualizar el análisis.","request.retry":"Reintentar","product.loading":"Cargando tus datos…","product.close":"Cerrar"};
const t=(key:string)=>uiMessages[key];
export function Button({variant="primary",busy=false,className="",children,...props}:ComponentProps<"button"> & {variant?:"primary"|"secondary"|"ghost";busy?:boolean}) {return <button type="button" {...props} aria-busy={busy || undefined} disabled={busy || props.disabled} className={`pl-button pl-button--${variant} ${className}`}>{busy && <span className="pl-spinner" aria-hidden="true"/>}{children}</button>;}
export function Card({className="",...props}:ComponentProps<"section">){return <section {...props} className={`pl-panel ${className}`}/>;}
export function Input(props:ComponentProps<"input">){return <input {...props} className={`pl-input ${props.className ?? ""}`}/>;}
export function Select(props:ComponentProps<"select">){return <select {...props} className={`pl-input ${props.className ?? ""}`}/>;}
export function Status({tone="info",children}:{tone?:"info"|"success"|"warning"|"error";children:ReactNode}){return <span className={`pl-status pl-status--${tone}`}>{children}</span>;}
export function SectionHeader({title,description}:{title:string;description?:string}){return <div className="pl-section-heading"><h2>{title}</h2>{description && <p>{description}</p>}</div>;}
export function EmptyState(){return <p role="status" className="pl-state">{t("widget.empty")}</p>;}
export function ErrorState({message,onRetry}:{message?:string;onRetry?:()=>void}){return <div role="alert" className="pl-state pl-state--error"><p>{message ?? t("widget.error")}</p>{onRetry && <Button variant="secondary" onClick={onRetry}>{t("request.retry")}</Button>}</div>;}
export function LoadingState({message}:{message?:string}){return <p role="status" className="pl-state pl-loading"><span className="pl-spinner" aria-hidden="true"/>{message ?? t("product.loading")}</p>;}
export function Toast({children,tone="info"}:{children:ReactNode;tone?:"info"|"success"|"error"}){return <div role={tone === "error" ? "alert" : "status"} aria-live={tone === "error" ? "assertive" : "polite"} className={children ? `pl-toast pl-toast--${tone}` : "sr-only"}>{children}</div>;}
export function Dialog({open,onClose,title,children}:{open:boolean;onClose:()=>void;title:string;children:ReactNode}){
 const ref=useRef<HTMLDialogElement>(null);const titleId=useId();
 useEffect(()=>{const node=ref.current;if(open && !node?.open)node?.showModal();else if(!open && node?.open)node.close();},[open]);
 return <dialog ref={ref} aria-labelledby={titleId} className="pl-dialog" onCancel={onClose} onClose={onClose}><div className="pl-dialog-heading"><h2 id={titleId}>{title}</h2><Button variant="ghost" aria-label={t("product.close")} onClick={onClose}>{t("product.close")}</Button></div>{children}</dialog>;
}

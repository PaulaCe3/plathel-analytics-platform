"use client";
import { useEffect, useMemo, useState } from "react";
import { ProductHeader, JourneyNavigation } from "@plathel/ui/product-header";
import { Button, Select, ErrorState, LoadingState } from "@plathel/ui/primitives";
import { EChartsBase } from "@plathel/ui/charts/echarts-base";
import { apiRequest } from "@/lib/api/client";
import type { components } from "@/types/api.generated";
type Options=components["schemas"]["ForecastOptions"];
type Result=components["schemas"]["ForecastResult"];
const month=(period:string|undefined)=>period?new Intl.DateTimeFormat("es-AR",{month:"long",year:"numeric",timeZone:"UTC"}).format(new Date(`${period.slice(0,7)}-01T00:00:00Z`)):"—";
const number=(value:number|null|undefined)=>value==null?"—":new Intl.NumberFormat("es-AR",{maximumFractionDigits:2}).format(value);
const range=(point:NonNullable<Result["prediction"]>[number]|undefined)=>point?.lower!=null&&point?.upper!=null?`${number(point.lower)} a ${number(point.upper)}`:"—";

export function ForecastWorkspace({datasetId,embedded=false}:{datasetId?:string;embedded?:boolean}) {
 const [options,setOptions]=useState<Options|null>(null),[result,setResult]=useState<Result|null>(null),[field,setField]=useState(""),[horizon,setHorizon]=useState(3),[busy,setBusy]=useState(false),[error,setError]=useState("");
 useEffect(()=>{
  if(!datasetId)return;let active=true;
  async function load(){
   try{const value=await apiRequest<Options>(`/api/v1/forecast/datasets/${encodeURIComponent(datasetId!)}/options`);if(!active)return;setOptions(value);const first=value.choices?.find(choice=>choice.available)?.field ?? "";setField(first);
    if(embedded&&first){setBusy(true);const prediction=await apiRequest<Result>(`/api/v1/forecast/datasets/${encodeURIComponent(datasetId!)}/prediction`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({field:first,horizon:3})});if(active)setResult(prediction);}
   }catch{if(active)setError("No pudimos recuperar la estimación. Intentá nuevamente.");}finally{if(active)setBusy(false);}
  }
  load();return()=>{active=false;};
 },[datasetId,embedded]);
 const chart=useMemo(()=>{const history=result?.history ?? [],prediction=result?.prediction ?? [],empty=history.map(()=>null),lower=prediction.map(point=>point.lower??null),span=prediction.map(point=>point.lower!=null&&point.upper!=null?point.upper-point.lower:null);return {animation:false,tooltip:{trigger:"axis" as const},legend:{top:0,data:["Datos observados","Predicción","Rango estimado"]},grid:{left:45,right:20,top:50,bottom:45,containLabel:true},xAxis:{type:"category" as const,axisLabel:{hideOverlap:true,formatter:(value:string)=>new Intl.DateTimeFormat("es-AR",{month:"short",year:"2-digit",timeZone:"UTC"}).format(new Date(`${value.slice(0,7)}-01T00:00:00Z`))},data:[...history.map(point=>point.period),...prediction.map(point=>point.period)]},yAxis:{type:"value" as const},series:[{name:"Datos observados",type:"line" as const,data:[...history.map(point=>point.value),...prediction.map(()=>null)],itemStyle:{color:"#3F4D3B"}},{name:"Base del rango",type:"line" as const,stack:"forecast-range",symbol:"none",lineStyle:{opacity:0},areaStyle:{opacity:0},tooltip:{show:false},data:[...empty,...lower]},{name:"Rango estimado",type:"line" as const,stack:"forecast-range",symbol:"none",lineStyle:{opacity:0},areaStyle:{color:"#93A18D",opacity:.28},tooltip:{show:false},data:[...empty,...span]},{name:"Predicción",type:"line" as const,data:[...history.map((point,index)=>index===history.length-1?point.value:null),...prediction.map(point=>point.value)],lineStyle:{type:"dashed" as const},itemStyle:{color:"#596B52"}}]};},[result]);
 async function predict(){if(!datasetId||busy)return;setBusy(true);setError("");try{setResult(await apiRequest<Result>(`/api/v1/forecast/datasets/${encodeURIComponent(datasetId)}/prediction`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({field,horizon})}));}catch{setError("No pudimos crear la estimación. Intentá nuevamente.");}finally{setBusy(false);}}
 const content=<section className={`pl-dashboard-section pl-forecast-summary ${options?.status==="unavailable"?"is-unavailable":""}`} aria-label="Predicciones">
  {options?.status!=="unavailable"&&<h2 id="forecast-title">Qué podría pasar después</h2>}
  {!datasetId?<><p>Primero cargá y prepará tus datos. Te mostraremos qué podemos estimar con tu historial.</p><a className="pl-button pl-button--primary" href="/bi">Cargar datos</a></>:<>
   {error&&<ErrorState message={error} onRetry={()=>options?predict():window.location.reload()}/>}
   {!options&&!error&&<LoadingState message="Revisando si podemos estimar los próximos meses…"/>}
   {options?.status==="unavailable"&&<div role="status" className="pl-forecast-unavailable"><p>Todavía no hay suficiente historial para estimar qué podría pasar después.</p><details className="pl-details"><summary>Ver por qué</summary><p>{options.explanation}</p></details></div>}
   {options?.status==="ok"&&<>
    <div className="pl-filter-fields"><label className="pl-filter-control">Valor mensual<Select value={field} disabled={busy} onChange={event=>{setField(event.target.value);setResult(null);}}>{(options.choices??[]).filter(choice=>choice.available).map(choice=><option key={choice.field} value={choice.field}>{choice.label}</option>)}</Select></label><label className="pl-filter-control">¿Cuánto tiempo hacia adelante?<Select value={horizon} disabled={busy} onChange={event=>{setHorizon(Number(event.target.value));setResult(null);}}>{[1,2,3,4,5,6].map(months=><option key={months} value={months}>{months} {months===1?"mes":"meses"}</option>)}</Select></label><Button variant={embedded?"secondary":"primary"} busy={busy} onClick={predict}>{busy?"Preparando la estimación…":result?"Actualizar estimación":"Crear estimación"}</Button></div>
    {result&&<div aria-live="polite">{result.status==="unavailable"?<p role="status">{result.explanation}</p>:<>
     <div className="pl-panel"><h3>Predicción para los próximos {result.horizon} {result.horizon===1?"mes":"meses"}</h3><p className="pl-kpi-value">{number(result.prediction?.[0]?.value)} <span className="pl-analysis-meta">para {month(result.prediction?.[0]?.period)}</span></p>{result.prediction?.[0]?.lower!=null&&result.prediction?.[0]?.upper!=null&&<p>Rango estimado: {range(result.prediction[0])}</p>}<EChartsBase option={chart} label="Histórico mensual observado, predicción y rango estimado"/>
      <details className="pl-details"><summary>Ver predicción como tabla</summary><div className="overflow-x-auto"><table><caption>Predicción de {result.label}</caption><thead><tr><th scope="col">Mes</th><th scope="col">Estimación</th><th scope="col">Rango estimado</th></tr></thead><tbody>{(result.prediction??[]).map(point=><tr key={point.period}><th scope="row">{month(point.period)}</th><td>{number(point.value)}</td><td>{range(point)}</td></tr>)}</tbody></table></div></details>
     </div>
     <div className="pl-chart-interpretation"><h3>Qué significa</h3><p>{result.interpretation}</p><p>Es una estimación, no una certeza. El rango resume la incertidumbre observada en pruebas históricas y no garantiza que el valor futuro quede dentro.</p></div>
     <details className="pl-details"><summary>¿Cómo se calculó?</summary><p>{result.explanation}</p><h3>Precisión histórica</h3><p>En las pruebas, la predicción tuvo un error promedio de aproximadamente {number(result.evaluation_value??undefined)} en las unidades de {result.label.toLowerCase()}. Se comprobó sobre datos históricos; el error futuro puede ser distinto.</p><p>Método seleccionado: {result.model}.</p><p>Datos utilizados: {result.observations} meses de datos observados · {result.history?.[0]?.period} a {result.history?.at(-1)?.period}. Horizonte evaluado: {result.horizon} meses.</p><p>{result.evaluation_metric}: {number(result.evaluation_value??0)} en las unidades de {result.label.toLowerCase()}, sobre {result.evaluation_periods} predicciones históricas sin usar datos futuros.</p><ul>{(result.limitations??[]).map(text=><li key={text}>{text}</li>)}</ul></details>
    </>}</div>}
   </>}
  </>}
 </section>;
 return embedded?content:<div className="pl-shell"><ProductHeader/><JourneyNavigation current={2} datasetId={datasetId}/><main className="pl-main"><div className="pl-page-heading"><h1>Tu negocio, en pocas palabras</h1><p>Estimaciones a partir de los datos que ya preparaste.</p></div>{content}{datasetId&&<a className="pl-button pl-button--primary" href={`/bi/${datasetId}/results`}>Ver todos los resultados</a>}</main></div>;
}

"use client";
import { t } from "@/lib/i18n";

import { useRouter } from "next/navigation";
import { Button, Select, Card, Status, LoadingState, ErrorState, SectionHeader } from "@/components/ui/primitives";
import { readyColumnKeys, humanMessage, fieldLabel } from "@/lib/presentation";
import { useEffect, useState } from "react";

import { ColumnMapping, MappingView, changeDatasetProfile, getMapping, saveMapping } from "@/lib/api/mapping";
import { ProfileSummary, getProfiles } from "@/lib/api/profiles";

function proposedMappings(view: MappingView): ColumnMapping[] {
  return view.columns.map((column) => {
    const suggestion = view.suggestions.find((item) => item.column_key === column.key);
    const candidate = suggestion?.candidates?.[0];
    if (candidate && candidate.score >= 0.6) {
      return { column_key: column.key, target_field: candidate.field_id, disposition: "canonical", options: {} };
    }
    return { column_key: column.key, target_field: null, disposition: suggestion?.suggested_disposition ?? "ignored", options: {} };
  });
}

export function ColumnMapper({ datasetId }: { datasetId: string }) {
  const router=useRouter();
  const [error,setError]=useState("");
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [view, setView] = useState<MappingView | null>(null);
  const [mappings, setMappings] = useState<ColumnMapping[]>([]);
  const [status, setStatus] = useState(t("column-mapper.action1"));
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    Promise.all([getProfiles(), getMapping(datasetId)])
      .then(([available, current]) => {
        setProfiles(available);
        setView(current);
        setMappings(current.mappings.length ? current.mappings : proposedMappings(current));
        setStatus(t("column-mapper.text1"));
      })
      .catch(() => setError(t("product.columnLoadError")))
      .finally(() => setBusy(false));
  }, [datasetId]);

  async function changeProfile(profileId: string) {
    setError("");
    setBusy(true);
    setStatus(t("column-mapper.text3"));
    try {
      await changeDatasetProfile(datasetId, profileId);
      const current = await getMapping(datasetId);
      setView(current);
      setMappings(proposedMappings(current));
      setStatus(t("column-mapper.text4"));
    } catch {
      setError(t("column-mapper.text5"));
    } finally {
      setBusy(false);
    }
  }

  function updateColumn(columnKey: string, value: string) {
    setMappings((current) => current.map((mapping) => {
      if (mapping.column_key !== columnKey) return mapping;
      if (value.startsWith("field:")) return { ...mapping, disposition: "canonical", target_field: value.slice(6) };
      return { ...mapping, disposition: value as ColumnMapping["disposition"], target_field: null };
    }));
  }

  async function save() {
    if(!view || busy)return;
    setError("");setBusy(true);setStatus(t("column-mapper.text6"));
    try{const saved=await saveMapping(datasetId,view.profile.id,mappings);setView(saved);setMappings(saved.mappings);setStatus(t("column-mapper.text7"));router.push(`/bi/${datasetId}/review`);}catch{setError(t("product.columnError"));}finally{setBusy(false);}
  }
  if (!view) return error ? <ErrorState message={error} onRetry={()=>window.location.reload()}/> : <LoadingState message={status}/>;
  const mappingByColumn=new Map(mappings.map(mapping=>[mapping.column_key,mapping]));
  const ready=readyColumnKeys(view,mappings);
  function publicLabel(fieldId:string) {const field=view!.profile.fields.find(item=>item.id===fieldId);const automatic=fieldId.replaceAll("_"," ").replace(/\b\w/g,char=>char.toUpperCase());return field && field.label!==automatic ? field.label : fieldLabel(fieldId);}
  function renderColumn(column:MappingView["columns"][number]) {
   const suggestion=view!.suggestions.find(item=>item.column_key===column.key)?.candidates?.[0];const mapping=mappingByColumn.get(column.key);const selected=mapping?.disposition === "canonical" ? `field:${mapping.target_field}` : mapping?.disposition ?? "ignored";
   const name=column.original_name || t("product.fieldFallback");
   return <div key={column.key} className="pl-column-row"><div><h3>{name}</h3><p>{t("product.examples")}: {(column.sample ?? []).slice(0,3).join(" · ") || t("column-mapper.text18")}</p></div><div><label htmlFor={`column-${column.key}`}>{t("product.whatColumn")}</label><Select id={`column-${column.key}`} aria-label={`${t("home.columns")}: ${name}`} value={selected} disabled={busy} onChange={event=>updateColumn(column.key,event.target.value)}>{view!.profile.fields.map(field=><option key={field.id} value={`field:${field.id}`}>{publicLabel(field.id)}</option>)}<option value="custom_dimension">{t("product.otherData")}</option><option value="custom_measure">{t("product.numericValue")}</option><option value="ignored">{t("product.unusedColumn")}</option></Select>{suggestion && <details><summary>{t("product.why")}</summary><p>{t("product.autoDetected")}: {publicLabel(suggestion.field_id)}. {humanMessage((suggestion.reasons ?? []).join(" "))}</p></details>}</div></div>;
  }
  return <div aria-busy={busy}><div className="pl-profile"><label>{t("column-mapper.text12")} <Select aria-label={t("column-mapper.text13")} value={view.profile.id} disabled={busy} onChange={event=>changeProfile(event.target.value)}>{profiles.map(profile=><option key={profile.id} value={profile.id}>{profile.name}</option>)}</Select></label><p>{view.profile.description}</p></div>
   <div className="pl-column-summary"><strong>{view.columns.length} {t("product.columnsFound")}</strong><Status tone="success">{ready.size} {t("product.identified")}</Status><Status tone={ready.size<view.columns.length ? "warning" : "info"}>{view.columns.length-ready.size} {t("product.needReview")}</Status></div>
   {ready.size>0 && <Card><SectionHeader title={`${ready.size} ${t("product.readyColumns")}`}/><ul className="pl-compact-columns">{view.columns.filter(column=>ready.has(column.key)).slice(0,7).map(column=><li key={column.key}><span aria-hidden="true">✓ </span>{publicLabel(mappingByColumn.get(column.key)?.target_field ?? "")}</li>)}</ul><details className="pl-details"><summary>{t("product.seeAll")}</summary>{view.columns.filter(column=>ready.has(column.key)).map(renderColumn)}</details></Card>}
   {ready.size<view.columns.length && <Card><SectionHeader title={t("product.needReview")}/>{view.columns.filter(column=>!ready.has(column.key)).map(renderColumn)}</Card>}
   {view.conflicts.length>0 && <div role="alert" className="pl-state pl-state--error">{view.conflicts.map((conflict,i)=><p key={i}>{humanMessage(conflict.message,Object.fromEntries(view.columns.map(column=>[column.key,column.original_name])))}</p>)}</div>}
   {error && <ErrorState message={error}/>}<div className="pl-actions"><a className="pl-button pl-button--secondary" href="/bi">{t("product.back")}</a><Button busy={busy} onClick={save}>{busy ? t("column-mapper.text6") : t("product.continue")}</Button><span role="status">{error ? "" : status}</span></div>
  </div>;
}

"use client";
import { t } from "@/lib/i18n";

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
      .catch((error) => setStatus(error instanceof Error ? error.message : t("column-mapper.text2")))
      .finally(() => setBusy(false));
  }, [datasetId]);

  async function changeProfile(profileId: string) {
    setBusy(true);
    setStatus(t("column-mapper.text3"));
    try {
      await changeDatasetProfile(datasetId, profileId);
      const current = await getMapping(datasetId);
      setView(current);
      setMappings(proposedMappings(current));
      setStatus(t("column-mapper.text4"));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : t("column-mapper.text5"));
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
    if (!view) return;
    setBusy(true);
    setStatus(t("column-mapper.text6"));
    try {
      const saved = await saveMapping(datasetId, view.profile.id, mappings);
      setView(saved);
      setMappings(saved.mappings);
      setStatus(t("column-mapper.text7"));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : t("column-mapper.text8"));
    } finally {
      setBusy(false);
    }
  }

  if (!view) return <p role="status" className="rounded-xl bg-white p-6 text-slate-700">{status}</p>;
  const mappingByColumn = new Map(mappings.map((mapping) => [mapping.column_key, mapping]));
  const levelLabel = { required: t("column-mapper.text9"), recommended: t("column-mapper.text10"), optional: t("column-mapper.text11") };

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <label className="text-sm font-semibold text-slate-800">{t("column-mapper.text12")}<select aria-label={t("column-mapper.text13")} className="ml-3 rounded-lg border border-slate-300 px-3 py-2" value={view.profile.id} disabled={busy} onChange={(event) => changeProfile(event.target.value)}>
            {profiles.map((profile) => <option key={profile.id} value={profile.id}>{profile.name}</option>)}
          </select>
        </label>
        <p className="mt-3 text-sm text-slate-600">{view.profile.description}</p>
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 p-6"><h2 className="text-xl font-semibold">{t("column-mapper.text14")}</h2><p className="mt-1 text-sm text-slate-600">{t("column-mapper.text15")}</p></div>
        <div className="divide-y divide-slate-100">
          {view.columns.map((column) => {
            const suggestion = view.suggestions.find((item) => item.column_key === column.key)?.candidates?.[0];
            const mapping = mappingByColumn.get(column.key);
            const selected = mapping?.disposition === "canonical" ? `field:${mapping.target_field}` : mapping?.disposition ?? "ignored";
            return <div key={column.key} className="grid gap-4 p-5 md:grid-cols-[1fr_1.2fr]">
              <div><p className="font-semibold text-slate-900">{column.original_name || column.key} <span className="font-normal text-slate-600">({column.key})</span></p><p className="mt-1 text-sm text-slate-600">{t("column-mapper.text16")}{(column.sample ?? []).slice(0, 3).join(t("column-mapper.text17")) || t("column-mapper.text18")}</p></div>
              <div>
                <select aria-label={`Mapping de ${column.original_name}`} value={selected} onChange={(event) => updateColumn(column.key, event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2">
                  {view.profile.fields.map((field) => <option key={field.id} value={`field:${field.id}`}>{field.label} — {levelLabel[field.level as keyof typeof levelLabel]}</option>)}
                  <option value="custom_dimension">{t("column-mapper.text19")}</option><option value="custom_measure">{t("column-mapper.text20")}</option><option value="ignored">{t("column-mapper.text21")}</option>
                </select>
                {suggestion && <div className="mt-2 text-xs text-slate-600"><strong>{suggestion.confidence === "high" ? t("column-mapper.text22") : suggestion.confidence === "medium" ? t("column-mapper.text23") : t("column-mapper.text24")}{t("column-mapper.text25")}{Math.round(suggestion.score * 100)} %).</strong> {(suggestion.reasons ?? []).join(t("column-mapper.text26"))}</div>}
              </div>
            </div>;
          })}
        </div>
      </section>

      {view.conflicts.length > 0 && <section className="rounded-xl border border-red-200 bg-red-50 p-4"><h2 className="font-semibold">{t("column-mapper.text27")}</h2>{view.conflicts.map((conflict, index) => <p key={`${conflict.code}-${index}`} className="mt-1 text-sm">{conflict.severity.toUpperCase()}: {conflict.message}</p>)}</section>}
      <div className="flex flex-wrap items-center gap-4"><button disabled={busy} onClick={save} className="rounded-xl bg-slate-950 px-5 py-3 font-semibold text-white disabled:opacity-40">{t("column-mapper.action2")}</button>{view.stage === "mapped" && <a href={`/bi/${datasetId}/review`} className="rounded-xl border border-slate-300 px-5 py-3 font-semibold">{t("column-mapper.action3")}</a>}<span role="status" className="text-sm text-slate-600">{status}</span></div>
    </div>
  );
}

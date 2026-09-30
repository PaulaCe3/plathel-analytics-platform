import type { components } from "@/types/api.generated";
import { messages, t } from "@/lib/i18n";
type MappingView=components["schemas"]["MappingResponse"];
export function readyColumnKeys(view:MappingView,mappings:components["schemas"]["ColumnMapping"][]):Set<string>{return new Set(view.columns.filter(column=>{const suggestion=view.suggestions.find(item=>item.column_key===column.key)?.candidates?.[0];const mapping=mappings.find(item=>item.column_key===column.key);return suggestion?.confidence === "high" && mapping?.disposition === "canonical" && mapping.target_field===suggestion.field_id && !view.conflicts.some(conflict=>conflict.column_key===column.key || conflict.field_id===mapping.target_field);}).map(column=>column.key));}
export function fieldLabel(field:string,terminology:Record<string,string>={}){return terminology[field] ?? messages[`field.${field}`] ?? (field.startsWith("custom:") ? field.slice(7).replaceAll("_"," ") : t("product.otherData"));}
export function humanMessage(text:string,terminology:Record<string,string>={}){const names={...Object.fromEntries(Object.entries(messages).filter(([key])=>key.startsWith("field.")).map(([key,value])=>[key.slice(6),value])),...terminology};return text.replace(/\b[a-z][a-z0-9_]*\b/g,word=>names[word] ?? word);}
export function actionLabel(id:string){return messages[`product.${id}`] ?? t("product.changeApplied");}

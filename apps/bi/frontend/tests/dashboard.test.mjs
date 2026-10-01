import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import ts from "typescript";
import { renderToStaticMarkup } from "react-dom/server";
import { createElement } from "react";
function compile(relative, replacements = {}) {
  let output = ts.transpileModule(fs.readFileSync(new URL(relative, import.meta.url), "utf8"), { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX } }).outputText;
  for (const dependency of ["react/jsx-runtime", "react"]) output = output.replaceAll(`from "${dependency}"`, `from ${JSON.stringify(import.meta.resolve(dependency))}`);
  for (const [name, url] of Object.entries(replacements)) output = output.replaceAll(JSON.stringify(name), JSON.stringify(url));
  return "data:text/javascript;base64," + Buffer.from(output).toString("base64");
}
const adapter = compile("../src/components/charts/adapters/dashboard.ts");
const messages = compile("../src/lib/i18n.ts");
const primitives=compile("../../../../packages/ui/src/primitives.tsx", {"@/lib/i18n":messages});
const presentation=compile("../src/lib/presentation.ts", {"@/lib/i18n":messages});
const chart = compile("../../../../packages/ui/src/charts/echarts-base.tsx");
const { chartOption } = await import(adapter);
const { DashboardRenderer, ErrorState, EmptyState } = await import(compile("../src/components/dashboard-renderer.tsx", { "@/components/charts/echarts-base": chart, "@/components/charts/adapters/dashboard": adapter, "@/lib/i18n": messages, "@/components/ui/primitives":primitives, "@/lib/presentation":presentation }));
const render = (type, props) => renderToStaticMarkup(createElement(type, props));
function dashboard(widgets, data) { return { spec: { sections: [{ id: "summary", title_key: "section.executive_summary", widgets }], terminology: {} }, data }; }
const widget = (type, id = "test") => ({ id, type, title_key: "metric.revenue", layout: { span: 3 } });
test("error and empty states announce meaningful Spanish messages", () => {
  assert.match(render(ErrorState), /role="alert".*No pudimos/);
  assert.match(render(EmptyState), /role="status".*No hay datos/);
});
test("KPI formats zero and signed comparison without treating zero as empty", () => {
  const html = render(DashboardRenderer, { dashboard: dashboard([widget("kpi")], { test: { status: "ok", value: 0, format: { type: "number", decimals: 0 }, excluded_rows: 1, comparison: { status:"ok", delta_pct: -0.25, direction:"decrease" } } }) });
  assert.match(html, />0<\/p>/); assert.match(html, /-25/); assert.match(html, /período anterior/);
});
for (const [type, status] of [["unknown", "ok"], ["ranking", "error"], ["kpi", "empty"], ["kpi", "unavailable"]]) test(`${type}/${status} renders a safe fallback`, () => {
  const html = render(DashboardRenderer, { dashboard: dashboard([widget(type)], { test: { status } }) });
  if(status === "empty" || status === "unavailable")assert.doesNotMatch(html,/pl-kpi-value|No hay datos/);else assert.match(html,/No pudimos/);
  assert.doesNotMatch(html, /undefined|traceback/);
});
test("empty section stays renderable", () => assert.doesNotMatch(render(DashboardRenderer, { dashboard: dashboard([], {}) }), /<section|No hay datos/));
test("chart has textual description and table from the same aggregated values", () => {
  const html = render(DashboardRenderer, { dashboard: dashboard([widget("ranking")], { test: { status: "ok", chart: "ranking", series: [{ key: "revenue", points: [["A", 123], ["B", 45]] }] } }) });
  assert.match(html, /aria-label="Ingresos"/); assert.match(html, /Ver como tabla/); assert.match(html, /<td>123<\/td>/); assert.match(html, /<td>45<\/td>/);
});
for (const type of ["timeseries", "ranking"]) test(`chart adapter preserves ${type} categories and values`, () => {
  const option = chartOption({ chart: type, series: [{ points: [["A", 10], ["B", -2]] }] });
  assert.deepEqual(option.series[0].data, [10, -2]);
  assert.deepEqual((type === "timeseries" ? option.xAxis : option.yAxis).data, ["A", "B"]);
});
test("chart adapter handles no series", () => assert.deepEqual(chartOption({ chart: "ranking", series: [] }).series[0].data, []));

test("single-series chart omits redundant legend but retains metric in tooltip", () => {
  const option = chartOption({ chart: "ranking", series: [{ points: [["A", 1]] }] }, "Ingresos");
  assert.equal(option.legend.show, false); assert.equal(option.series[0].name, "Ingresos");
});

test("insights render localized templates without exposing keys or JSON", () => {
  const html = render(DashboardRenderer, { dashboard: dashboard([widget("insights")], { test: { status: "ok", insights: [{ id: "channel", template_key: "insight.channel_dominance", text: "insight.channel_dominance", params: { channel: "Online", share: 2 / 3 } }] } }) });
  assert.match(html, /El canal Online concentra el 66,7/);
  assert.doesNotMatch(html, /insight\.channel_dominance|&quot;share&quot;/);
});

test("dashboard first view limits KPIs and keeps remaining metrics in details",()=>{
 const widgets=Array.from({length:8},(_,i)=>widget("kpi",`kpi${i}`));const data=Object.fromEntries(widgets.map(w=>[w.id,{status:"ok",value:10,format:{type:"number",decimals:0},excluded_rows:0}]));
 const html=render(DashboardRenderer,{dashboard:dashboard(widgets,data)});assert.equal((html.split("Otras métricas")[0].match(/pl-kpi-value/g)??[]).length,5);assert.match(html,/Más indicadores/);
});
test("chart adapter uses the PLATHEL palette",()=>assert.deepEqual(chartOption({chart:"ranking",series:[]}).color,["#596B52","#3F4D3B","#75866C","#98A590","#BEC6B8"]));

const {readyColumnKeys,humanMessage}=await import(presentation);
test("column presentation distinguishes confident matches and ambiguous columns without changing mappings",()=>{
 const mappings=[{column_key:"c01",disposition:"canonical",target_field:"amount"},{column_key:"c02",disposition:"canonical",target_field:"date"}];const before=JSON.stringify(mappings);
 const view={columns:[{key:"c01"},{key:"c02"}],suggestions:[{column_key:"c01",candidates:[{field_id:"amount",confidence:"high",score:.96}]},{column_key:"c02",candidates:[{field_id:"date",confidence:"medium",score:.75}]}],conflicts:[]};
 assert.deepEqual([...readyColumnKeys(view,mappings)],["c01"]);assert.equal(JSON.stringify(mappings),before);view.conflicts=[{column_key:"c01"}];assert.equal(readyColumnKeys(view,mappings).size,0);
});
test("visible explanations translate field IDs without altering user values",()=>assert.equal(humanMessage("Se convirtió amount al tipo decimal."),"Se convirtió Importe al tipo decimal."));

test("Hallazgos shows three initially and retains additional useful findings",()=>{
 const items=Array.from({length:5},(_,i)=>({id:`finding${i}`,template_key:"insight.leader_share",params:{value:`Grupo ${i}`,share:.4},text:"internal"}));
 const html=render(DashboardRenderer,{dashboard:dashboard([widget("insights")],{test:{status:"ok",insights:items}})});
 assert.equal((html.split("Ver más")[0].match(/<li/g)??[]).length,3);
 assert.match(html,/Grupo 4/);
});

test("results explains with four KPIs and three findings, without BI charts",()=>{
const widgets=[...Array.from({length:6},(_,i)=>widget("kpi",`k${i}`)),widget("timeseries","chart"),widget("insights","findings")];const data=Object.fromEntries(widgets.map(w=>[w.id,w.type==="kpi"?{status:"ok",value:1,format:{type:"number",decimals:0}}:w.type==="insights"?{status:"ok",insights:Array.from({length:5},(_,i)=>({id:String(i),template_key:"insight.leader_share",params:{value:`Grupo ${i}`,share:.5}}))}:{status:"ok",series:[]} ]));
const html=render(DashboardRenderer,{dashboard:dashboard(widgets,data),mode:"results"});assert.equal((html.match(/class="dashboard-widget pl-kpi"/g)??[]).length,0);assert.equal((html.match(/<strong>/g)??[]).length,2);assert.equal((html.match(/<li/g)??[]).length,3);assert.match(html,/Lo más importante/);assert.doesNotMatch(html,/Gráficos clave|Ver como tabla|Elegir qué explorar/);
});

test("dashboard removes findings already explained by the visible chart",()=>{
const finding={id:"peak",template_key:"insight.peak_period",params:{period:"2026-02",value:99}};const value=dashboard([widget("timeseries","line"),widget("insights","findings")],{line:{status:"ok",chart:"timeseries",series:[],interpretation:finding},findings:{status:"ok",insights:[finding]}});const html=render(DashboardRenderer,{dashboard:value});assert.equal((html.match(/fue el período/g)??[]).length,1);assert.doesNotMatch(html,/>Hallazgos</);
});
test("selection highlights preserve chart values and accessible distinction",()=>{const option=chartOption({chart:"ranking",series:[{points:[["A",10],["B",20]]}]},"Ingresos",["B"]);assert.deepEqual(option.series[0].data.map(point=>point.value),[10,20]);assert.equal(option.series[0].data[1].itemStyle.borderWidth,2);});

const {datePreset}=await import(compile("../src/lib/date-presets.ts"));
test("period presets use the dataset calendar, clamp bounds and handle leap dates",()=>{
 assert.deepEqual(datePreset("3","2020-01-01","2024-03-31"),["2024-01-01","2024-03-31"]);
 assert.deepEqual(datePreset("30d","2020-01-01","2024-03-01"),["2024-02-01","2024-03-01"]);
 assert.deepEqual(datePreset("12","2024-02-01","2024-03-31"),["2024-02-01","2024-03-31"]);
 assert.deepEqual(datePreset("year","2020-01-01","2024-03-31"),["2024-01-01","2024-03-31"]);
 assert.equal(chartOption({chart:"timeseries",series:[]}).legend.show,false);
});

test("comparison presentation uses backend pp and zero baseline absolute values",()=>{
 const metric={status:"ok",value:.45,format:{type:"percent",decimals:1},comparison:{mode:"previous_period",status:"ok",delta_pp:5,delta_pct:null,previous_value:.4,direction:"increase",current_range:{from:"2025-02-01",to:"2025-02-28"},previous_range:{from:"2025-01-01",to:"2025-01-31"}}};
 const html=render(DashboardRenderer,{dashboard:dashboard([widget("kpi")],{test:metric})});assert.match(html,/\+5 puntos porcentuales/);assert.doesNotMatch(html,/12,5/);assert.match(html,/2025-01-31/);
 const zero={...metric,value:120,format:{type:"currency",currency:"ARS",decimals:0},comparison:{status:"previous_zero",delta_abs:120,delta_pct:null,previous_value:0}};
 assert.match(render(DashboardRenderer,{dashboard:dashboard([widget("kpi")],{test:zero})}),/120.*vs\. período anterior/);
 const partial={...metric,comparison:{...metric.comparison,partial_period:true,warnings:[{code:"PARTIAL_PREVIOUS_PERIOD"}]}};assert.match(render(DashboardRenderer,{dashboard:dashboard([widget("kpi")],{test:partial})}),/período actual incompleto/);
 const missing={...zero,comparison:{status:"insufficient_data",reason_key:"comparison.insufficient_data"}};
 assert.doesNotMatch(render(DashboardRenderer,{dashboard:dashboard([widget("kpi")],{test:missing})}),/Sin comparación|N\/A|vs\. período anterior/);
 assert.match(render(DashboardRenderer,{dashboard:dashboard([widget("kpi")],{test:metric}),mode:"results"}),/\+5 puntos porcentuales/);
});


test("F2 renders authoritative backend copy and at most three primary findings",()=>{
 const insights=Array.from({length:5},(_,i)=>({id:`fact${i}`,kind:"change",template_key:"business.fact",text:`Facturación aumentó ${i+2} % respecto del período anterior.`,params:{relative_delta:99+i,metric_label:"inventado"}}));
 const d=dashboard([widget("insights")],{test:{status:"ok",insights}});
 const html=render(DashboardRenderer,{dashboard:d,mode:"results"});
 assert.equal((html.match(/Facturación aumentó/g)??[]).length,3);
 assert.doesNotMatch(html,/inventado|9900|business.fact/);
 assert.match(render(DashboardRenderer,{dashboard:d,mode:"dashboard"}),/Ver más/);
});


test("F2 deduplicates concentration already interpreted by a visible chart",()=>{
 const local={id:"local",template_key:"insight.top_n_concentration",dimension:"field.category",params:{top_n:3,share:.9}};
 const fact={id:"fact",kind:"concentration",template_key:"business.fact",dimension:"category",text:"No duplicar",params:{top_n:3,share:.9,current:null}};
 const d=dashboard([widget("ranking","chart"),widget("insights","findings")],{chart:{status:"ok",chart:"ranking",series:[],interpretation:local},findings:{status:"ok",insights:[fact]}});
 assert.doesNotMatch(render(DashboardRenderer,{dashboard:d,mode:"dashboard"}),/No duplicar|>Hallazgos</);
 assert.match(render(DashboardRenderer,{dashboard:d,mode:"results"}),/No duplicar/);
});

test("F3 presents backend anomaly copy inside the shared three-finding limit",()=>{
 const anomaly={id:"anomaly",kind:"anomaly_high",template_key:"business.fact",text:"Diciembre tuvo facturación inusualmente alta frente al patrón histórico observado.",params:{period:"2024-12",observed:300,baseline:100,direction:"alto"}};
 const insights=[anomaly,...Array.from({length:4},(_,i)=>({id:`other${i}`,kind:"leadership",template_key:"business.fact",text:`Hallazgo ${i}`,params:{segment:String(i)}}))];
 const html=render(DashboardRenderer,{dashboard:dashboard([widget("insights")],{test:{status:"ok",insights}}),mode:"results"});
 assert.match(html,/inusualmente alta frente al patrón histórico observado/);
 assert.equal((html.match(/<li/g)??[]).length,3);
 assert.doesNotMatch(html,/modified_z|significativo|porque/);
});

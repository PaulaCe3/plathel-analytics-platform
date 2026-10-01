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
  const html = render(DashboardRenderer, { dashboard: dashboard([widget("kpi")], { test: { status: "ok", value: 0, format: { type: "number", decimals: 0 }, excluded_rows: 1, comparison: { delta_pct: -0.25 } } }) });
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

test("chart has a textual metric legend", () => {
  const option = chartOption({ chart: "ranking", series: [{ points: [["A", 1]] }] }, "Ingresos");
  assert.deepEqual(option.legend.data, ["Ingresos"]); assert.equal(option.series[0].name, "Ingresos");
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

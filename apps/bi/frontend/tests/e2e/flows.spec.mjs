import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { python } from "../../playwright.config.mjs";
const api = "http://127.0.0.1:8100/api/v1";
test.beforeEach(async ({ page }) => {
  const errors = []; page.on("pageerror", (error) => errors.push(error.message));
  page.__errors = errors;
});
test.afterEach(async ({ page }) => expect(page.__errors).toEqual([]));
async function accessible(page) {
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations.map(({ id, nodes }) => ({ id, nodes: nodes.map((node) => node.target) }))).toEqual([]);
}
async function clean(page) {
  await expect(page.getByRole("button", { name: "Preparar mis datos" })).toBeEnabled();
  await accessible(page);
  await page.getByRole("button", { name: "Preparar mis datos" }).focus();
  await page.keyboard.press("Enter");
  await page.getByRole("link", { name: "Ver resultados" }).click();
  await expect(page.getByRole("heading", { name: "Esto es lo que encontramos", exact: true })).toBeVisible();
  await page.getByRole("link",{name:"Explorar dashboard",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Explorá tus datos",exact:true}).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Resumen", exact: true })).toBeVisible();
  await expect(page.locator("canvas").first()).toBeVisible();
}
function kpi(page, name) { return page.getByRole("article").filter({ has: page.getByRole("heading", { name, exact: true }) }).first(); }
async function exportFile(page, testInfo, format, expectedRows) {
  await page.getByRole("button", {name:"Exportar",exact:true}).click();
  await page.getByLabel("Formato de exportación").selectOption(format);
  await accessible(page);
  const downloadEvent = page.waitForEvent("download");
  await expect(page.getByRole("button", { name: "Descargar", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Descargar", exact: true }).focus();
  await page.keyboard.press("Enter");
  const download = await downloadEvent;
  expect(await download.failure()).toBeNull();
  const output = testInfo.outputPath(`datos.${format}`); await download.saveAs(output);
  const bytes = await fs.readFile(output); expect(bytes.length).toBeGreaterThan(20);
  if (format === "csv") {
    expect(bytes.toString("utf8")).toContain("Venta");
    expect(bytes.toString("utf8").trim().split(/\r?\n/).length).toBe(expectedRows + 1);
  } else {
    execFileSync(python, ["-c", "import sys; from openpyxl import load_workbook; w=load_workbook(sys.argv[1],read_only=True); assert w.sheetnames==['Datos','Registro de cambios','Resumen']; assert sum(1 for _ in w['Datos'].values)==int(sys.argv[2])+1; w.close()", output, String(expectedRows)]);
  }
  await page.getByRole("button", {name:"Cerrar",exact:true}).click();
}
async function responsive(page) {
  for (const width of [390, 768, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    const span = await page.getByRole("article").first().evaluate((node) => getComputedStyle(node).gridColumnStart);
    expect(span).toBe(`span ${width < 768 ? 12 : width < 1024 ? 6 : 3}`);
  }
}
for (const [demo, profile, metric, expected] of [["retail_demo", "retail_ecommerce", "Ingresos", "264.000"], ["services_demo", "services", "Horas de servicio", "36"], ["hospitality_demo", "hospitality", "Noches totales", "24"]]) {
  test(`archivo propio ${profile}: mapping, limpieza, filtros, accesibilidad, descarga y borrado`, async ({ page, request }, testInfo) => {
    const fixture = new URL(`../../../backend/demo_data/${demo}/data.csv`, import.meta.url);
    let source = await fs.readFile(fixture, "utf8");
    if (profile === "hospitality") source = source.replace(/,ARS(?=\r?\n|$)/, ",USD");
    const metadata = JSON.parse(await fs.readFile(new URL(`../../../backend/demo_data/${demo}/demo.json`, import.meta.url), "utf8"));
    const response = await page.goto("/bi");
    expect(response.headers()["x-content-type-options"]).toBe("nosniff");
    expect(response.headers()["content-security-policy"]).toContain("frame-ancestors 'none'");
    if (process.env.E2E_PRODUCTION === "true") expect(response.headers()["content-security-policy"]).not.toContain("unsafe-eval");
    await accessible(page);
    await page.getByLabel("Archivo de datos").setInputFiles({ name: "propio.csv", mimeType: "text/csv", buffer: Buffer.from(source) });
    await page.getByRole("button", { name: "Continuar" }).click();
    await page.getByRole("link", { name: "Revisar columnas" }).click();
    const dataset = page.url().split("/").at(-2);
    await page.getByRole("combobox", { name: "Rubro", exact: true }).selectOption(profile);
    await expect(page.getByRole("status").filter({ hasText: "Las sugerencias se recalcularon" })).toBeVisible();
    const headers = source.split(/\r?\n/)[0].split(",");
    if(await page.getByText("Ver todas", {exact:true}).count()) await page.getByText("Ver todas", {exact:true}).click();
    for (const [index, mapping] of metadata.preset_mapping.entries()) await page.getByLabel(`Revisar columnas: ${headers[index]}`, { exact: true }).selectOption(mapping.disposition === "canonical" ? `field:${mapping.target_field}` : mapping.disposition);
    await accessible(page);
    await page.getByRole("button", { name: "Continuar", exact: true }).focus(); await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/review$/);
    await clean(page);
    await expect(kpi(page, metric)).toContainText(expected);
    const filterSummary = page.getByText("Filtros", { exact: true });
    await filterSummary.focus(); await page.keyboard.press("Enter");
    await expect(page.getByRole("combobox", { name: "Canal", exact: true })).toBeHidden();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("combobox", { name: "Canal", exact: true })).toBeVisible();
    if (profile === "hospitality") {await page.getByText("Más filtros",{exact:true}).click(); await expect(page.getByLabel("Entrada desde", { exact: true })).toHaveAttribute("min", "2026-01-02");}
    if (profile === "services") {await page.getByText("Elegir qué explorar",{exact:true}).click();const option=page.getByRole("combobox",{name:"Ver datos por"}); const value=await option.locator("option").filter({hasText:"Servicio"}).first().getAttribute("value"); await option.selectOption(value);await expect(page.getByRole("heading", { name: "Servicio", exact: true }).last()).toBeVisible();}
    if (profile === "hospitality") {
      await expect(page.getByRole("heading", { name: "Tarifa diaria promedio", exact: true })).toHaveCount(0);
      await page.getByRole("combobox", { name: "Moneda", exact: true }).selectOption("ARS");
      await expect(kpi(page, "Tarifa diaria promedio")).toBeVisible();
      await expect(page.getByText("11 de 12 filas", { exact: true })).toBeVisible();
      await exportFile(page, testInfo, "xlsx", 11);
    } else {
      await page.getByRole("combobox", { name: "Canal", exact: true }).selectOption("Online");
      await expect(page.getByText("8 de 12 filas", { exact: true })).toBeVisible();
      if (profile === "retail_ecommerce") await expect(kpi(page, "Ingresos")).toContainText("176.000");
      await exportFile(page, testInfo, profile === "retail_ecommerce" ? "csv" : "xlsx", 8);
    }
    await page.getByText("Ver como tabla", { exact: true }).first().click();
    await expect(page.getByRole("table").first()).toBeVisible();
    await responsive(page);
    await page.getByRole("button", { name: "Terminar y borrar mis datos" }).focus(); await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/bi\?deleted=1/);
    await expect(page.getByRole("status").filter({ hasText: "La sesión anterior fue eliminada" })).toBeVisible();
    expect((await request.get(`${api}/datasets/${dataset}`)).status()).toBe(404);
  });
}
test("demo real, filtro y XLSX", async ({ page }, testInfo) => {
  await page.goto("/bi");
  await page.getByText("Probar con datos de ejemplo",{exact:true}).click();
  await page.getByRole("button", { name: "Probar Retail", exact: true }).click();
  await expect(page).toHaveURL(/review$/);
  await clean(page);
  await expect(page.getByText("Modo demo · Datos sintéticos.", { exact: false })).toBeVisible();
  await page.getByRole("combobox", { name: "Canal", exact: true }).selectOption("Online");
  await expect(page.getByText("8 de 12 filas", { exact: true })).toBeVisible();
  await exportFile(page, testInfo, "xlsx", 8);
  await page.getByRole("button", { name: "Terminar y borrar mis datos" }).click();
  await expect(page).toHaveURL(/deleted=1/);
});

test("sesión no disponible vuelve a entrada con mensaje", async ({ page }) => {
  await page.goto(`/bi/${"x".repeat(32)}/dashboard`);
  await expect(page).toHaveURL(/\/bi\?expired=1/);
  await expect(page.getByRole("status").filter({ hasText: "La sesión venció o ya no está disponible" })).toBeVisible();
  await accessible(page);
});

test("error al aplicar filtro se anuncia y permite reintentar", async ({ page, request }) => {
  const created = await request.post(`${api}/datasets/demo`, { data: { demo_id: "retail_demo" } });
  expect(created.status()).toBe(201); const { dataset_id: dataset } = await created.json();
  expect((await request.post(`${api}/datasets/${dataset}/validate`)).status()).toBe(200);
  expect((await request.put(`${api}/datasets/${dataset}/cleaning`, { data: { actions: [] } })).status()).toBe(200);
  await page.goto(`/bi/${dataset}/dashboard`);
  await expect(kpi(page, "Ingresos")).toContainText("264.000");
  await page.route("**/api/v1/datasets/*/dashboard", (route) => route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ error: { code: "INTERNAL_ERROR", message: "No pudimos aplicar los filtros.", details: [], request_id: "test" } }) }), { times: 1 });
  await page.getByRole("combobox", { name: "Canal", exact: true }).selectOption("Online");
  await expect(page.getByRole("main").getByRole("alert")).toContainText("No pudimos aplicar los filtros.");
  await accessible(page);
  await page.getByRole("button", { name: "Reintentar", exact: true }).focus(); await page.keyboard.press("Enter");
  await expect(kpi(page, "Ingresos")).toContainText("176.000");
  await expect(page.getByRole("button", { name: "Reintentar", exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Terminar y borrar mis datos" }).click();
  await expect(page).toHaveURL(/deleted=1/);
});

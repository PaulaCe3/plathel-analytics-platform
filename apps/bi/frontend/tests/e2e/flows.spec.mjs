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
for (const [name, metric] of [["Retail / E-commerce", "Ventas"], ["Servicios", "Horas de servicio"], ["Hotelería", "Noches totales"]]) {
  test(`demo pública ${name}: preparación, resultados y dashboard`, async ({ page, request }) => {
    const response = await page.goto("/bi");
    expect(response.headers()["x-content-type-options"]).toBe("nosniff");
    expect(response.headers()["content-security-policy"]).toContain("frame-ancestors 'none'");
    if (process.env.E2E_PRODUCTION === "true") expect(response.headers()["content-security-policy"]).not.toContain("unsafe-eval");
    await accessible(page);
    const card = page.getByRole("article").filter({ has: page.getByRole("heading", { name, exact: true }) });
    await card.getByRole("button", { name: /^Explorar demo/ }).click();
    await expect(page).toHaveURL(/\/results$/);
    await expect(page).not.toHaveURL(/\/(mapping|review)$/);
    const dataset = page.url().split("/").at(-2);
    await expect(page.getByRole("heading", { name: "Tu negocio, en pocas palabras", exact: true })).toBeVisible();
    await accessible(page);
    await page.getByRole("link",{name:"Explorar mis datos",exact:true}).click();
    await expect(page.getByRole("heading",{name:"Explorá tus datos",exact:true}).first()).toBeVisible();
    await expect(kpi(page, metric)).toBeVisible();
    await expect(page.locator("canvas").first()).toBeVisible();
    await accessible(page);
    await page.getByText("Opciones",{exact:true}).click(); await page.getByRole("button", { name: "Terminar y borrar mis datos" }).focus(); await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/bi\?deleted=1/);
    await expect(page.getByRole("status").filter({ hasText: "La sesión anterior fue eliminada" })).toBeVisible();
    expect((await request.get(`${api}/datasets/${dataset}`)).status()).toBe(404);
  });
}
test("demo real, filtro y XLSX", async ({ page }, testInfo) => {
  await page.goto("/bi");
  const retail = page.getByRole("article").filter({ has: page.getByRole("heading", { name: "Retail / E-commerce", exact: true }) });
  await retail.getByRole("button", { name: /^Explorar demo/ }).click();
  await expect(page).toHaveURL(/results$/);
  await page.getByRole("link",{name:"Explorar mis datos",exact:true}).click();
  await expect(page.getByText("DEMO",{exact:true})).toBeVisible();
  await page.getByRole("combobox", { name: "Canal", exact: true }).selectOption("Online");
  await expect(page.getByRole("button",{name:"Exportar",exact:true})).toBeEnabled();
  await exportFile(page, testInfo, "xlsx", 72);
  await page.getByText("Opciones",{exact:true}).click(); await page.getByRole("button", { name: "Terminar y borrar mis datos" }).click();
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
  await expect(kpi(page, "Ventas")).toContainText("264.000");
  await page.route("**/api/v1/datasets/*/dashboard", (route) => route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ error: { code: "INTERNAL_ERROR", message: "No pudimos aplicar los filtros.", details: [], request_id: "test" } }) }), { times: 1 });
  await page.getByRole("combobox", { name: "Canal", exact: true }).selectOption("Online");
  await expect(page.getByRole("main").getByRole("alert")).toContainText("No pudimos aplicar los filtros.");
  await accessible(page);
  await page.getByRole("button", { name: "Reintentar", exact: true }).focus(); await page.keyboard.press("Enter");
  await expect(kpi(page, "Ventas")).toContainText("176.000");
  await expect(page.getByRole("button", { name: "Reintentar", exact: true })).toHaveCount(0);
  await page.getByText("Opciones",{exact:true}).click(); await page.getByRole("button", { name: "Terminar y borrar mis datos" }).click();
  await expect(page).toHaveURL(/deleted=1/);
});

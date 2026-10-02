import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("home pública: solo ofrece las tres demos y explica su alcance", async ({ page }) => {
  await page.goto("/bi");
  await expect(page.getByRole("heading", { name: "Explorá PLATHEL", exact: true })).toBeVisible();
  await expect(page.getByLabel("Archivo de datos")).toHaveCount(0);
  await expect(page.getByText(/CSV|XLSX|Subí tus datos/)).toHaveCount(0);
  for (const name of ["Retail / E-commerce", "Servicios", "Hotelería"]) {
    await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  }
  await expect(page.getByRole("button", { name: /^Explorar demo/ })).toHaveCount(3);
  await expect(page.getByText(/demostración simplificada.*datos de ejemplo/i)).toBeVisible();
  for (const width of [390, 768, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});

test("home pública: la demo se activa por teclado y abre Resultados sin pasos técnicos", async ({ page }) => {
  await page.goto("/bi");
  const retail = page.getByRole("article").filter({ has: page.getByRole("heading", { name: "Retail / E-commerce", exact: true }) });
  const button = retail.getByRole("button", { name: /^Explorar demo/ });
  await expect(button).toBeEnabled();
  await button.focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/bi\/[^/]+\/results$/);
  await expect(page).not.toHaveURL(/\/(mapping|review)$/);
  await expect(page.getByRole("heading", { name: "Tu negocio, en pocas palabras", exact: true })).toBeVisible();
});

test("home: el aviso de sesión eliminada vence y conserva otros parámetros", async ({ page }) => {
  await page.goto("/bi?deleted=1&test=preserved");
  await expect(page.getByRole("status").filter({ hasText: "La sesión anterior fue eliminada" })).toBeVisible();
  await expect(page.getByText("La sesión anterior fue eliminada", { exact: false })).not.toBeVisible({ timeout: 10000 });
  await expect(page).toHaveURL(/test=preserved$/);
});

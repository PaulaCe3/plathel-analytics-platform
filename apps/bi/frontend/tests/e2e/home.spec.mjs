import { test, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { python } from "../../playwright.config.mjs";
import AxeBuilder from "@axe-core/playwright";
test("home: hero, navigation, responsive and accessibility",async({page})=>{
 await page.goto("/bi");await expect(page.getByRole("button",{name:/36 meses/})).toHaveCount(0);
 await expect(page.getByRole("heading",{name:"Subí tus datos",exact:true})).toBeVisible();
 await expect(page.getByRole("button",{name:"Seleccionar archivo",exact:true})).toBeVisible();
 await expect(page.getByRole("main")).not.toContainText(/Preparado para distintos|Todo listo para analizar|Convertí tus datos/);
 await expect(page.getByRole("button",{name:"Probar Retail"})).toBeHidden();
 await page.getByText("Probar con datos de ejemplo",{exact:true}).click();await expect(page.getByRole("button",{name:"Probar Retail"})).toBeEnabled();
 for(const width of [390,768,1280]) {await page.setViewportSize({width,height:900});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);await page.screenshot({path:`${process.env.TEMP}/plathel-data-${width}.png`,fullPage:true});}
 expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
});
test("home: selection, change, accessible loading and upload error",async({page})=>{
 await page.goto("/bi");await expect(page.getByText("CSV o XLSX · Máximo 20 MB")).toBeVisible();
 await page.locator("#dataset-file").setInputFiles({name:"ventas.csv",mimeType:"text/csv",buffer:Buffer.from("fecha,venta\n2026-01-01,10")});
 await expect(page.locator(".home-dropzone strong")).toContainText("ventas.csv");await expect(page.getByRole("button",{name:"Continuar",exact:true})).toBeEnabled();
 const chooser=page.waitForEvent("filechooser");await page.getByRole("button",{name:"Cambiar archivo"}).click();await (await chooser).setFiles({name:"otras.csv",mimeType:"text/csv",buffer:Buffer.from("a,b\n1,2")});await expect(page.locator(".home-dropzone strong")).toContainText("otras.csv");
 await page.route("**/api/v1/datasets",async route=>{await new Promise(resolve=>setTimeout(resolve,700));await route.fulfill({status:415,contentType:"application/json",body:JSON.stringify({error:{code:"FILE_CORRUPT",message:"internal",request_id:"test"}})});});
 await page.getByRole("button",{name:"Continuar",exact:true}).click();await expect(page.getByRole("status").filter({hasText:"Preparando tus datos"})).toBeVisible();await expect(page.getByRole("alert").filter({hasText:"No pudimos leer este archivo"})).toBeVisible();
});
test("home: drop selection and invalid file feedback",async({page})=>{
 await page.goto("/bi");await expect(page.getByText("CSV o XLSX · Máximo 20 MB")).toBeVisible();
 await page.locator(".home-dropzone").evaluate(element=>{const transfer=new DataTransfer();transfer.items.add(new File(["a,b\n1,2"],"arrastrado.csv",{type:"text/csv"}));element.dispatchEvent(new DragEvent("drop",{bubbles:true,dataTransfer:transfer}));});await expect(page.locator(".home-dropzone strong")).toContainText("arrastrado.csv");
 await page.locator("#dataset-file").setInputFiles({name:"archivo.exe",mimeType:"application/octet-stream",buffer:Buffer.from("invalid")});await expect(page.getByRole("alert").filter({hasText:"Probá con CSV o XLSX"})).toBeVisible();
});
test("home: deleted toast expires and preserves other query parameters",async({page})=>{
 await page.goto("/bi?deleted=1&test=preserved");await expect(page.getByRole("status").filter({hasText:"La sesión anterior fue eliminada"})).toBeVisible();
 await expect(page.getByText("La sesión anterior fue eliminada",{exact:false})).not.toBeVisible({timeout:10000});await expect(page).toHaveURL(/test=preserved$/);
});

test("home: real XLSX upload retains sheet selection and column navigation",async({page,request})=>{
 const buffer=execFileSync(python,["-c","import io,sys; from openpyxl import Workbook; w=Workbook(); w.active.title='Ventas'; w.active.append(['fecha','venta']); w.active.append(['2026-01-01',100]); s=w.create_sheet('Otros'); s.append(['fecha','venta']); s.append(['2026-01-02',200]); b=io.BytesIO(); w.save(b); sys.stdout.buffer.write(b.getvalue())"]);
 await page.goto("/bi");await expect(page.getByText("CSV o XLSX · Máximo 20 MB")).toBeVisible();
 await page.locator("#dataset-file").setInputFiles({name:"ventas.xlsx",mimeType:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",buffer});
 await page.getByRole("button",{name:"Continuar",exact:true}).click();await expect(page.getByRole("heading",{name:"Tu archivo está listo para revisar"})).toBeVisible();
 await page.getByRole("combobox").selectOption("Otros");await expect(page.getByRole("status").filter({hasText:"Hoja actualizada"})).toBeVisible();
 const link=page.getByRole("link",{name:"Revisar columnas",exact:true});const href=await link.getAttribute("href");await link.click();await expect(page).toHaveURL(/\/mapping$/);
 await request.delete(`http://127.0.0.1:8100/api/v1/datasets/${href.split('/')[2]}`);
});

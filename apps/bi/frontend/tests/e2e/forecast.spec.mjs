import {test,expect} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
const api="http://127.0.0.1:8100/api/v1";
async function ready(request,months){
 const rows=Array.from({length:months},(_,i)=>`${2020+Math.floor(i/12)}-${String(i%12+1).padStart(2,"0")}-01,${i%12+1},${(i%12+1)*10}`);
 const uploaded=await request.post(`${api}/datasets`,{multipart:{file:{name:"historial.csv",mimeType:"text/csv",buffer:Buffer.from(`fecha,cantidad,importe\n${rows.join("\n")}`)}}});expect(uploaded.status()).toBe(201);const id=(await uploaded.json()).dataset_id;
 expect((await request.put(`${api}/datasets/${id}/mapping`,{data:{profile_id:"custom",mappings:[{column_key:"c01",target_field:"date",disposition:"canonical"},{column_key:"c02",target_field:"quantity",disposition:"canonical"},{column_key:"c03",target_field:"amount",disposition:"canonical"}]}})).status()).toBe(200);
 expect((await request.post(`${api}/datasets/${id}/validate`)).status()).toBe(200);
 expect((await request.put(`${api}/datasets/${id}/cleaning`,{data:{actions:[]}})).status()).toBe(200);return id;
}
test("Predicciones: guía inicial y datos insuficientes sin inventar resultado",async({page,request})=>{
 await page.goto("/forecast");await expect(page.getByRole("heading",{name:"Predicciones",exact:true})).toBeVisible();await expect(page.getByRole("link",{name:"Preparar mis datos"})).toHaveAttribute("href","/bi");
 const id=await ready(request,12);try{await page.goto(`/forecast?dataset=${id}`);await expect(page.getByRole("heading",{name:"Todavía no podemos crear una predicción"})).toBeVisible();await expect(page.getByRole("button",{name:"Crear estimación"})).toHaveCount(0);expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);}finally{await request.delete(`${api}/datasets/${id}`);}
});
test("Predicciones: historial real, horizonte, evaluación y accesibilidad",async({page,request})=>{
 const id=await ready(request,36);try{await page.goto(`/bi/${id}/dashboard`);await page.getByRole("link",{name:"Predicciones",exact:true}).click();await expect(page).toHaveURL(new RegExp(`forecast\\?dataset=${id}`));await expect(page.getByRole("heading",{name:"¿Qué querés predecir?"})).toBeVisible();await page.getByLabel("Valor mensual").selectOption("quantity");await page.getByLabel("¿Cuánto tiempo hacia adelante?").selectOption("6");await page.getByRole("button",{name:"Crear estimación"}).focus();await page.keyboard.press("Enter");await expect(page.getByRole("heading",{name:"01 / Predicción"})).toBeVisible();await expect(page.getByText("36 meses de datos observados",{exact:false})).toBeVisible();await expect(page.locator("canvas")).toBeVisible();await page.getByText("Ver como tabla",{exact:true}).click();await expect(page.getByRole("table")).toBeVisible();await expect(page.getByRole("cell",{name:"Predicción",exact:true})).toHaveCount(6);await page.getByText("Cómo se calculó",{exact:true}).click();await expect(page.getByText(/Error absoluto medio: 0/)).toBeVisible();
 for(const width of [1280,768,390]){await page.setViewportSize({width,height:900});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);}
 await page.getByLabel("¿Cuánto tiempo hacia adelante?").selectOption("1");await expect(page.getByRole("heading",{name:"01 / Predicción"})).toHaveCount(0);
 }finally{await request.delete(`${api}/datasets/${id}`);}
});

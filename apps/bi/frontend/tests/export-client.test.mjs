import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import ts from "typescript";

// Exercise the real TS helpers with native Response/Blob and a minimal download DOM.
function compile(relative, replacement) {
  let output = ts.transpileModule(fs.readFileSync(new URL(relative, import.meta.url), "utf8"), { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText;
  if (output.includes('"@/lib/i18n"')) output = output.replace('"@/lib/i18n"', JSON.stringify(i18nUrl));
  if (replacement) output = output.replace('"./client"', JSON.stringify(replacement));
  return "data:text/javascript;base64," + Buffer.from(output).toString("base64");
}
const i18nUrl = compile("../src/lib/i18n.ts");
const clientUrl = compile("../src/lib/api/client.ts");
const { apiDownload, apiRequest } = await import(clientUrl);
const { downloadDataset } = await import(compile("../src/lib/api/exports.ts", clientUrl));


test("binary export uses POST, preserves filters and releases Object URLs", async (t) => {
  const calls = [], created = [], revoked = [];
  t.mock.method(globalThis, "fetch", async (url, options) => { calls.push([url, options]); return new Response(new Uint8Array([80, 75, 3, 4]), { headers: { "Content-Disposition": 'attachment; filename="datos.xlsx"', "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" } }); });
  t.mock.method(URL, "createObjectURL", (blob) => { created.push(blob); return "blob:test"; });
  t.mock.method(URL, "revokeObjectURL", (url) => revoked.push(url));
  const link = { click() { this.clicked = true; }, remove() { this.removed = true; } };
  globalThis.document = { createElement: () => link, body: { appendChild: () => {} } };
  globalThis.window = { setTimeout: (callback) => callback() };
  t.after(() => { delete globalThis.document; delete globalThis.window; });
  const filters = [{ field: "location", op: "in", values: ["Córdoba"] }, { field: "channel", op: "in", values: ["Online"] }];
  await downloadDataset("dataset123", { format: "xlsx", scope: "filtered_data", filters, headers: "friendly", include_original_columns: true });
  assert.ok(calls[0][0].endsWith("/api/v1/datasets/dataset123/export"));
  assert.equal(calls[0][1].method, "POST");
  assert.deepEqual(JSON.parse(calls[0][1].body).filters, filters);
  assert.equal(created[0].size, 4);
  assert.equal(link.download, "datos.xlsx");
  assert.ok(link.clicked && link.removed);
  assert.deepEqual(revoked, ["blob:test"]);
});


test("download failures decode the existing error envelope", async (t) => {
  t.mock.method(globalThis, "fetch", async () => new Response(JSON.stringify({ error: { code: "DATASET_EXPIRED", message: "La sesión expiró.", details: [], request_id: "id" } }), { status: 410, headers: { "Content-Type": "application/json" } }));
  await assert.rejects(apiDownload("/export"), (error) => error.status === 410 && error.payload.error.code === "DATASET_EXPIRED" && error.message === "La sesión expiró.");
});


test("unsafe response filenames never become download paths", async (t) => {
  t.mock.method(globalThis, "fetch", async () => new Response("abc", { headers: { "Content-Disposition": 'attachment; filename="../../secret.csv"' } }));
  const result = await apiDownload("/export");
  assert.equal(result.filename, "datos");
  assert.equal(await result.blob.text(), "abc");
});


test("demo creation uses the real dataset endpoint and response contract", async (t) => {
  let request;
  t.mock.method(globalThis, "fetch", async (url, init) => { request = [url, init]; return Response.json({ dataset_id: "demo-session", stage: "mapped", demo_id: "retail_demo" }); });
  const { createDemo } = await import(compile("../src/lib/api/demos.ts", clientUrl));
  const result = await createDemo("retail_demo");
  assert.ok(request[0].endsWith("/api/v1/datasets/demo"));
  assert.deepEqual(JSON.parse(request[1].body), { demo_id: "retail_demo" });
  assert.equal(result.dataset_id, "demo-session");
  assert.equal(result.stage, "mapped");
});


test("JSON client keeps existing 204 behavior", async (t) => {
  t.mock.method(globalThis, "fetch", async () => new Response(null, { status: 204 }));
  assert.equal(await apiRequest("/delete", { method: "DELETE" }), undefined);
});

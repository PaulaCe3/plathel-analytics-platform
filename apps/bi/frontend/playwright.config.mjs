import { defineConfig } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
const directory = path.dirname(fileURLToPath(import.meta.url));
const backend = path.resolve(directory, "../backend");
export const python = process.env.E2E_PYTHON ?? path.join(backend, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
export default defineConfig({
  testDir: "./tests/e2e", timeout: 90000, expect: { timeout: 20000 }, workers: 1,
  use: { baseURL: "http://127.0.0.1:3100", ...(process.env.PLAYWRIGHT_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHANNEL } : {}), trace: "retain-on-failure", screenshot: "only-on-failure" },
  reporter: [["list"]],
  webServer: [
    { command: `"${python}" -m uvicorn platform_api:app --host 127.0.0.1 --port 8100 --no-access-log --no-proxy-headers`, cwd: backend, url: "http://127.0.0.1:8100/api/v1/health", timeout: 60000, env: { FRONTEND_ORIGIN: "http://127.0.0.1:3100", DATASET_STORAGE_PATH: ".data/e2e-sessions", UPLOADS_PER_HOUR: "200", MAX_SESSIONS_PER_IP: "100" } },
    { command: `node node_modules/next/dist/bin/next ${process.env.E2E_PRODUCTION === "true" ? "start" : "dev"} --hostname 127.0.0.1 --port 3100`, url: "http://127.0.0.1:3100/bi", timeout: 120000, env: { NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:8100" } },
  ],
});

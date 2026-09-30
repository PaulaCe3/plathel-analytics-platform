import path from "node:path";
import type { NextConfig } from "next";
const development = process.env.NODE_ENV !== "production";
const apiOrigin = new URL(process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").origin;
const csp = ["default-src 'self'", `script-src 'self' 'unsafe-inline'${development ? " 'unsafe-eval'" : ""}`, "style-src 'self' 'unsafe-inline'", "img-src 'self' data: blob:", `connect-src 'self' ${apiOrigin}${development ? " ws: wss:" : ""}`, "font-src 'self'", "object-src 'none'", "base-uri 'self'", "frame-ancestors 'none'", "form-action 'self'"].join("; ");
const nextConfig: NextConfig = {
  turbopack: { root: path.resolve(process.cwd(), "../../.."), resolveAlias: { react: "./node_modules/react", echarts: "./node_modules/echarts" } },
  reactStrictMode: true,
  async headers() {
    return [{ source: "/:path*", headers: [
      { key: "Content-Security-Policy", value: csp },
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "no-referrer" },
      { key: "X-Frame-Options", value: "DENY" },
      { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
      ...(process.env.HTTPS_DEPLOYMENT === "true" && !development ? [{ key: "Strict-Transport-Security", value: "max-age=31536000" }] : []),
    ] }];
  },
};
export default nextConfig;

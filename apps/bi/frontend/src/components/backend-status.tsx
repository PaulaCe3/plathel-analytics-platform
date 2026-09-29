"use client";

import { useEffect, useState } from "react";

import { getHealth, getMeta, type MetaResponse } from "@/lib/api/system";

type ConnectionState =
  | { kind: "checking" }
  | { kind: "connected"; meta: MetaResponse }
  | { kind: "unavailable" };

export function BackendStatus() {
  const [state, setState] = useState<ConnectionState>({ kind: "checking" });

  useEffect(() => {
    const controller = new AbortController();

    async function checkBackend() {
      try {
        const [health, meta] = await Promise.all([
          getHealth(controller.signal),
          getMeta(controller.signal),
        ]);
        if (health.status === "ok") {
          setState({ kind: "connected", meta });
        } else {
          setState({ kind: "unavailable" });
        }
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "unavailable" });
      }
    }

    void checkBackend();
    return () => controller.abort();
  }, []);

  const connected = state.kind === "connected";

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5" aria-live="polite">
      <div className="flex items-center gap-3">
        <span
          className={`h-2.5 w-2.5 rounded-full ${
            connected
              ? "bg-emerald-500"
              : state.kind === "checking"
                ? "animate-pulse bg-amber-400"
                : "bg-rose-500"
          }`}
          aria-hidden="true"
        />
        <p className="font-medium text-slate-800">
          {connected
            ? "Backend conectado"
            : state.kind === "checking"
              ? "Verificando backend"
              : "Backend no disponible"}
        </p>
      </div>
      {connected ? (
        <p className="mt-3 text-sm text-slate-500">
          Límite inicial: {state.meta.max_file_mb} MB · Idioma: {state.meta.default_locale}
        </p>
      ) : null}
    </div>
  );
}

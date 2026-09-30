import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "PLATHEL · Business Intelligence",
  description: "PLATHEL — DATA · AI · AUTOMATION. Convertí tus datos en decisiones claras.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}

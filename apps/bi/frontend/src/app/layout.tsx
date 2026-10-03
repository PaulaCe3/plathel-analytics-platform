import localFont from "next/font/local";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import "../../../../../packages/ui/src/plathel.css";
import "./visual-polish.css";

const space=localFont({src:"../../../../../packages/ui/fonts/spacegrotesk.ttf",variable:"--font-space",display:"swap"});
const inter=localFont({src:"../../../../../packages/ui/fonts/inter.ttf",variable:"--font-inter",display:"swap"});
export const metadata: Metadata = {
  title: "PLATHEL · Business Intelligence",
  description: "PLATHEL — DATA · AI · AUTOMATION. Convertí tus datos en decisiones claras.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="es">
      <body className={`${space.variable} ${inter.variable}`}>{children}</body>
    </html>
  );
}

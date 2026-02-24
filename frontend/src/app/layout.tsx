import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import Nav from "@/components/layout/Nav";

const geist = Geist({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "BPÜ Pipeline", template: "%s | BPÜ Pipeline" },
  description: "KI-gestützte Datenextraktions-Pipeline für Berufsprüfungs-PDFs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className={`${geist.className} bg-slate-50 min-h-screen`}>
        <div className="flex min-h-screen">
          <Nav />
          <main className="flex-1 p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}

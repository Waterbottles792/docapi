import type { Metadata } from "next";
import "./globals.css";
import "./landing.css";
import SiteBackground from "@/components/landing/SiteBackground";

export const metadata: Metadata = {
  title: "docapi — Reliable document extraction for AI agents",
  description:
    "An open-source document-extraction API for AI agents. Give it a file and the fields you want; get JSON guaranteed to match your schema, or a precise structured error. Never silently-wrong data.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <SiteBackground />
        {children}
      </body>
    </html>
  );
}

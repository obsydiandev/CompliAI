import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CompliAI - EU AI Act Compliance Platform",
  description: "Build and maintain EU AI Act Annex IV technical documentation",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

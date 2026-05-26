import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Compiler System",
  description: "Natural language to validated executable application configurations",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}

import type { Metadata, Viewport } from "next";
import { business } from "@/lib/business";
import "./globals.css";

// Per Next.js 14: viewport + themeColor are a separate export from metadata.
// Putting them inside the metadata object emits a deprecation warning at build.
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#FDFBF7",
};

export const metadata: Metadata = {
  title: business.name,
  description: business.tagline,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Per-business accent color is wired via a CSS variable on <html> so all
  // accent-using components (.text-[var(--accent)], etc.) pick it up.
  return (
    <html
      lang="en"
      style={{ "--accent": business.accent_color } as React.CSSProperties}
    >
      <body>{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import QueryProvider from "@/providers/QueryProvider";
import "@fontsource/anton";
import "@fontsource/inter/400.css";
import "@fontsource/inter/700.css";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "NeroSentinel", template: "%s | NeroSentinel" },
  applicationName: "NeroSentinel",
  description: "Intelligent Water Intelligence & Drought Resilience Platform.",
  openGraph: { title: "NeroSentinel", description: "Intelligent Water Intelligence & Drought Resilience Platform.", siteName: "NeroSentinel", type: "website" },
  twitter: { card: "summary", title: "NeroSentinel", description: "Intelligent Water Intelligence & Drought Resilience Platform." },
  icons: { icon: [{ url: "/nerosentinel-mark.svg", type: "image/svg+xml" }] },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="min-h-full antialiased font-sans">
      <body className="min-h-full font-sans text-foreground bg-background">
        <QueryProvider>
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}

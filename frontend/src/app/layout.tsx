import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import { cn } from "@/lib/utils";
import NextTopLoader from "nextjs-toploader";
import { Toaster } from "sonner";
import Sidebar from "@/components/sidebar";

export const metadata: Metadata = {
  title: "Crypto Trading Agent",
  description: "AI-powered paper trading platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("dark font-sans", GeistSans.variable, GeistMono.variable)}>
      <body className="antialiased bg-background text-foreground min-h-screen">
        <NextTopLoader color="#3b82f6" showSpinner={false} />
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 p-8 overflow-auto">
            {children}
          </main>
        </div>
        <Toaster richColors position="bottom-right" />
      </body>
    </html>
  );
}

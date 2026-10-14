import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "PJ Selling | Smart Product Recommendations",
  description:
    "E-commerce demo with AI-powered product recommendations and co-buy analysis",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        className="min-h-screen text-gray-100 antialiased"
        style={{
          fontFamily: "'Inter', sans-serif",
          background:
            "linear-gradient(160deg, #0f172a 0%, #1e293b 40%, #0f172a 100%)",
        }}
      >
        {/* Subtle dot pattern overlay */}
        <div className="fixed inset-0 bg-dots opacity-30 pointer-events-none z-0" />
        <div className="relative z-10">
          <Header />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

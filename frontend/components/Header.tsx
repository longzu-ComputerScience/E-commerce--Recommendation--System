"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/", label: "Products", icon: "🛍️" },
  { href: "/recommendations", label: "Recommendations", icon: "🎯" },
  { href: "/forecast", label: "Forecast", icon: "📈" },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header
      className="sticky top-0 z-50"
      style={{
        background: "rgba(15, 23, 42, 0.85)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        borderBottom: "1px solid rgba(148, 163, 184, 0.1)",
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{
                background: "linear-gradient(135deg, #14b8a6, #0ea5e9)",
              }}
            >
              <span className="text-white text-sm font-bold">PJ</span>
            </div>
            <span className="text-lg font-extrabold tracking-tight gradient-text group-hover:opacity-80 transition-opacity">
              PJ Selling
            </span>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const isActive =
                link.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-300 ${
                    isActive
                      ? "text-white"
                      : "text-gray-400 hover:text-gray-200"
                  }`}
                  style={
                    isActive
                      ? {
                          background:
                            "linear-gradient(135deg, rgba(20, 184, 166, 0.15), rgba(14, 165, 233, 0.12))",
                          border: "1px solid rgba(20, 184, 166, 0.25)",
                          boxShadow: "0 0 12px rgba(20, 184, 166, 0.1)",
                        }
                      : {
                          border: "1px solid transparent",
                        }
                  }
                >
                  <span className="text-xs">{link.icon}</span>
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}

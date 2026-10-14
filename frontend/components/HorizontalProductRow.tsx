"use client";

import { useRef } from "react";
import { Product } from "@/lib/types";
import ProductCard from "./ProductCard";

interface HorizontalProductRowProps {
  products: Product[];
  title: string;
  badge?: string;
}

export default function HorizontalProductRow({
  products,
  title,
  badge,
}: HorizontalProductRowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const amount = scrollRef.current.clientWidth * 0.75;
    scrollRef.current.scrollBy({
      left: direction === "left" ? -amount : amount,
      behavior: "smooth",
    });
  };

  if (products.length === 0) {
    return (
      <div>
        <h2 className="text-xl font-bold text-gray-200 mb-3">{title}</h2>
        <p className="text-gray-400 text-sm py-6">No products to show.</p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in-up">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold gradient-text">{title}</h2>
          {badge && (
            <span
              className="text-[10px] font-medium px-2.5 py-0.5 rounded-full"
              style={{
                background:
                  "linear-gradient(135deg, rgba(20, 184, 166, 0.12), rgba(14, 165, 233, 0.12))",
                color: "#5eead4",
                border: "1px solid rgba(20, 184, 166, 0.2)",
              }}
            >
              {badge}
            </span>
          )}
        </div>
        <div className="flex gap-1.5">
          <button
            onClick={() => scroll("left")}
            className="p-2 rounded-lg transition-all duration-200 text-gray-400 hover:text-white"
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(148, 163, 184, 0.12)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "rgba(20, 184, 166, 0.4)";
              e.currentTarget.style.boxShadow =
                "0 0 10px rgba(20, 184, 166, 0.15)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "rgba(148, 163, 184, 0.12)";
              e.currentTarget.style.boxShadow = "none";
            }}
            aria-label="Scroll left"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>
          <button
            onClick={() => scroll("right")}
            className="p-2 rounded-lg transition-all duration-200 text-gray-400 hover:text-white"
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(148, 163, 184, 0.12)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "rgba(20, 184, 166, 0.4)";
              e.currentTarget.style.boxShadow =
                "0 0 10px rgba(20, 184, 166, 0.15)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "rgba(148, 163, 184, 0.12)";
              e.currentTarget.style.boxShadow = "none";
            }}
            aria-label="Scroll right"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto pb-3 scroll-smooth scrollbar-hide"
      >
        {products.map((product, idx) => (
          <div
            key={product.item_id}
            className="flex-shrink-0 w-48 animate-slide-in-right"
            style={{ animationDelay: `${idx * 50}ms` }}
          >
            <ProductCard product={product} />
          </div>
        ))}
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Product } from "@/lib/types";
import { getProduct } from "@/lib/api";
import RelatedProducts from "@/components/RelatedProducts";
import RecommendedProducts from "@/components/RecommendedProducts";

function formatPrice(price: number) {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
  }).format(price);
}

export default function ProductDetailPage() {
  const params = useParams();
  const itemId = params.id as string;
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getProduct(itemId)
      .then(setProduct)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [itemId]);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="skeleton rounded h-4 w-32 mb-6" />
        <div className="grid md:grid-cols-2 gap-8">
          <div className="skeleton rounded-2xl h-80" />
          <div className="space-y-4">
            <div className="skeleton rounded h-8 w-3/4" />
            <div className="skeleton rounded h-6 w-1/4" />
            <div className="skeleton rounded h-4 w-1/2" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="text-center py-16 animate-fade-in-up">
        <div className="text-5xl mb-4 animate-float">😕</div>
        <p className="text-red-400 mb-4 font-medium">
          Product not found or failed to load.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-teal-400 hover:text-teal-300 transition-colors"
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
          Back to products
        </Link>
      </div>
    );
  }

  const isDiaper = product.category_l1 === "Tã";

  return (
    <div className="animate-fade-in-up">
      {/* Breadcrumb */}
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-teal-400 hover:text-teal-300 mb-6 transition-colors group"
      >
        <svg
          className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform"
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
        Back to products
      </Link>

      {/* ── Product Detail ─────────────────────── */}
      <div
        className="grid md:grid-cols-2 gap-8 mb-12 rounded-2xl p-6 sm:p-8"
        style={{
          background: "rgba(30, 41, 59, 0.5)",
          border: "1px solid rgba(148, 163, 184, 0.1)",
        }}
      >
        {/* Image placeholder */}
        <div
          className="rounded-xl h-80 flex items-center justify-center relative overflow-hidden"
          style={{
            background:
              "linear-gradient(135deg, rgba(20, 184, 166, 0.12), rgba(14, 165, 233, 0.08), rgba(56, 189, 248, 0.04))",
          }}
        >
          <span className="text-8xl animate-float opacity-60">🛍️</span>
          <div
            className="absolute top-6 right-6 w-20 h-20 rounded-full animate-spin-slow opacity-20"
            style={{
              background:
                "radial-gradient(circle, rgba(20, 184, 166, 0.35), transparent)",
            }}
          />
          <div
            className="absolute bottom-8 left-8 w-14 h-14 rounded-full opacity-15"
            style={{
              background:
                "radial-gradient(circle, rgba(14, 165, 233, 0.4), transparent)",
              animation: "float 4s ease-in-out infinite reverse",
            }}
          />
        </div>

        {/* Product info */}
        <div className="flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            <span
              className="text-xs font-semibold px-3 py-1 rounded-full"
              style={{
                background:
                  "linear-gradient(135deg, rgba(20, 184, 166, 0.12), rgba(14, 165, 233, 0.12))",
                color: "#5eead4",
                border: "1px solid rgba(20, 184, 166, 0.2)",
              }}
            >
              {product.category_l1}
            </span>
            {product.sale_status === 1 && (
              <span
                className="text-xs font-semibold px-3 py-1 rounded-full"
                style={{
                  background:
                    "linear-gradient(135deg, rgba(52, 211, 153, 0.15), rgba(16, 185, 129, 0.15))",
                  color: "#6ee7b7",
                  border: "1px solid rgba(52, 211, 153, 0.2)",
                }}
              >
                ✨ On Sale
              </span>
            )}
            {isDiaper && product.normalized_size && (
              <span
                className="text-xs font-semibold px-3 py-1 rounded-full"
                style={{
                  background:
                    "linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(245, 158, 11, 0.15))",
                  color: "#fcd34d",
                  border: "1px solid rgba(251, 191, 36, 0.2)",
                }}
              >
                Size: {product.normalized_size}
              </span>
            )}
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-gray-100 mb-3 leading-tight">
            {product.category}
          </h1>

          <p className="text-3xl sm:text-4xl font-extrabold gradient-text mb-6">
            {formatPrice(product.price)}
          </p>

          <div
            className="space-y-3 text-sm rounded-xl p-4"
            style={{
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid rgba(148, 163, 184, 0.08)",
            }}
          >
            <div className="flex items-center gap-2">
              <span className="text-gray-500 w-28">Brand</span>
              <span className="text-gray-200 font-medium">
                {product.brand}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-500 w-28">Manufacturer</span>
              <span className="text-gray-200 font-medium">
                {product.manufacturer}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-500 w-28">Category</span>
              <span className="text-gray-300 font-medium text-xs">
                {product.category_l1} → {product.category_l2} →{" "}
                {product.category_l3}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-500 w-28">Item ID</span>
              <code
                className="text-xs px-2 py-0.5 rounded text-teal-300"
                style={{
                  background: "rgba(20, 184, 166, 0.1)",
                  border: "1px solid rgba(20, 184, 166, 0.2)",
                }}
              >
                {product.item_id}
              </code>
            </div>
          </div>
        </div>
      </div>

      {/* ── Section A: Solution 1 (Related Products) — mọi sản phẩm ── */}
      <div
        className="mb-10 pt-8"
        style={{ borderTop: "1px solid rgba(148, 163, 184, 0.08)" }}
      >
        <RelatedProducts itemId={itemId} />
      </div>

      {/* ── Section B: Solution 2 (Recommended Products) — chỉ hiển thị cho Tã ── */}
      {isDiaper && (
        <div
          className="pt-8"
          style={{ borderTop: "1px solid rgba(148, 163, 184, 0.08)" }}
        >
          <RecommendedProducts itemId={itemId} />
        </div>
      )}
    </div>
  );
}

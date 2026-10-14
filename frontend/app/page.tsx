"use client";

import { useState, useEffect, useCallback } from "react";
import { Product } from "@/lib/types";
import { getProducts, getCategories } from "@/lib/api";
import ProductGrid from "@/components/ProductGrid";
import SearchFilter from "@/components/SearchFilter";

const PAGE_SIZE = 20;

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-5">
      {Array.from({ length: PAGE_SIZE }).map((_, i) => (
        <div
          key={i}
          className="rounded-2xl p-4"
          style={{
            background: "rgba(30, 41, 59, 0.6)",
            border: "1px solid rgba(148, 163, 184, 0.08)",
          }}
        >
          <div className="skeleton rounded-xl h-36 mb-3" />
          <div className="skeleton rounded-full h-3 w-16 mb-2" />
          <div className="skeleton rounded h-4 w-full mb-1" />
          <div className="skeleton rounded h-4 w-3/4 mb-2" />
          <div className="skeleton rounded h-3 w-20 mb-3" />
          <div className="skeleton rounded h-5 w-24 mt-2" />
        </div>
      ))}
    </div>
  );
}

export default function HomePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategoriesList] = useState<string[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({ search: "", category: "" });

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProducts({
        page,
        page_size: PAGE_SIZE,
        category: filters.category || undefined,
        search: filters.search || undefined,
      });
      setProducts(data.products);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to fetch products:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load products. Make sure the backend is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  useEffect(() => {
    getCategories().then(setCategoriesList).catch(console.error);
  }, []);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handleFilterChange = (newFilters: {
    search: string;
    category: string;
  }) => {
    setFilters(newFilters);
    setPage(1);
  };

  return (
    <div className="animate-fade-in-up">
      {/* Hero section */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{
              background:
                "linear-gradient(135deg, rgba(20, 184, 166, 0.2), rgba(14, 165, 233, 0.2))",
              border: "1px solid rgba(20, 184, 166, 0.3)",
            }}
          >
            <span className="text-lg">🛍️</span>
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight gradient-text">
              Products
            </h1>
            <p className="text-gray-400 text-sm">
              Browse our full catalog of products
            </p>
          </div>
        </div>
      </div>

      <SearchFilter
        categories={categories}
        onFilterChange={handleFilterChange}
      />

      {/* Error state */}
      {error ? (
        <div
          className="rounded-2xl p-8 text-center animate-fade-in-up"
          style={{
            background:
              "linear-gradient(135deg, rgba(239, 68, 68, 0.08), rgba(220, 38, 38, 0.04))",
            border: "1px solid rgba(239, 68, 68, 0.2)",
          }}
        >
          <div className="text-4xl mb-3 animate-float">⚠️</div>
          <p className="text-red-400 font-semibold mb-1">
            Unable to load products
          </p>
          <p className="text-red-300/70 text-sm mb-5 max-w-md mx-auto">
            {error}
          </p>
          <button onClick={fetchProducts} className="btn-gradient px-6 py-2.5 text-sm inline-flex items-center gap-2">
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
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Try Again
          </button>
        </div>
      ) : loading ? (
        <SkeletonGrid />
      ) : (
        <>
          {/* Results info */}
          <div className="flex items-center justify-between mb-5">
            <p className="text-sm text-gray-400">
              <span className="font-semibold text-gray-200">
                {total.toLocaleString()}
              </span>{" "}
              products found
            </p>
            {totalPages > 1 && (
              <p className="text-sm text-gray-400">
                Page <span className="text-gray-200">{page}</span> of{" "}
                <span className="text-gray-200">{totalPages}</span>
              </p>
            )}
          </div>

          <ProductGrid products={products} />
        </>
      )}

      {/* Pagination */}
      {!loading && !error && totalPages > 1 && (
        <div className="flex justify-center items-center gap-3 mt-10 mb-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-medium text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed hover:text-white transition-all active:scale-[0.98]"
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(148, 163, 184, 0.12)",
            }}
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
            Previous
          </button>
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum: number;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (page <= 3) {
                pageNum = i + 1;
              } else if (page >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = page - 2 + i;
              }
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`w-10 h-10 rounded-lg text-sm font-medium transition-all duration-300 ${
                    page === pageNum ? "text-white" : "text-gray-400 hover:text-gray-200"
                  }`}
                  style={
                    page === pageNum
                      ? {
                          background:
                            "linear-gradient(135deg, #14b8a6, #0ea5e9)",
                          boxShadow: "0 0 12px rgba(20, 184, 166, 0.35)",
                        }
                      : {
                          background: "rgba(255, 255, 255, 0.03)",
                        }
                  }
                >
                  {pageNum}
                </button>
              );
            })}
          </div>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-medium text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed hover:text-white transition-all active:scale-[0.98]"
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(148, 163, 184, 0.12)",
            }}
          >
            Next
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
      )}
    </div>
  );
}

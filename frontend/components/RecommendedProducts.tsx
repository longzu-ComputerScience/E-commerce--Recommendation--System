"use client";

import { useState, useEffect } from "react";
import { Product } from "@/lib/types";
import { getRecommendations } from "@/lib/api";
import HorizontalProductRow from "./HorizontalProductRow";

export default function RecommendedProducts({ itemId }: { itemId: string }) {
  const [products, setProducts] = useState<Product[]>([]);
  const [strategy, setStrategy] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getRecommendations(itemId, 20)
      .then((data) => {
        const filtered = data.recommendations.filter((p) => p.item_id !== itemId);
        setProducts(filtered);
        setStrategy(data.strategy);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [itemId]);

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="skeleton rounded h-6 w-56 mb-4" />
        <div className="flex gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="flex-shrink-0 w-48 rounded-2xl h-60"
              style={{
                background: "rgba(30, 41, 59, 0.6)",
                border: "1px solid rgba(148, 163, 184, 0.08)",
              }}
            >
              <div className="skeleton rounded-xl h-32 m-3" />
              <div className="px-3 space-y-2">
                <div className="skeleton rounded-full h-3 w-16" />
                <div className="skeleton rounded h-3 w-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-red-400 text-sm glass-surface px-4 py-3">
        ⚠️ Failed to load Solution 2 recommendations.
      </p>
    );
  }

  return (
    <HorizontalProductRow
      products={products}
      title="Recommended Products (Solution 2)"
      badge={strategy}
    />
  );
}

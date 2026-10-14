"use client";

import { useState, useEffect } from "react";
import { ForecastResponse, ForecastPrediction } from "@/lib/types";
import { getForecast } from "@/lib/api";

const PAGE_SIZE = 50;

function formatPrice(price: number) {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
  }).format(price);
}

export default function ForecastPage() {
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getForecast()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const predictions = data?.predictions ?? [];
  const totalPages = Math.ceil(predictions.length / PAGE_SIZE);
  const paginated = predictions.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE
  );

  return (
    <div className="animate-fade-in-up">
      {/* Hero section */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{
              background:
                "linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.2))",
              border: "1px solid rgba(251, 191, 36, 0.3)",
            }}
          >
            <span className="text-lg">📈</span>
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight gradient-text">
              Quantity Forecast
            </h1>
            <p className="text-gray-400 text-sm">
              Solution 3 — LightGBM daily demand prediction
            </p>
          </div>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div
          className="rounded-2xl p-12 text-center"
          style={{
            background: "rgba(30, 41, 59, 0.5)",
            border: "1px solid rgba(148, 163, 184, 0.1)",
          }}
        >
          <div className="text-5xl mb-4 animate-float">🧠</div>
          <p className="text-gray-300 font-medium mb-1">
            Training LightGBM model...
          </p>
          <p className="text-gray-500 text-sm">
            This may take a minute on first load
          </p>
          <div className="mt-6 mx-auto w-48 h-1 rounded-full overflow-hidden"
            style={{ background: "rgba(255,255,255,0.06)" }}
          >
            <div
              className="h-full rounded-full"
              style={{
                background: "linear-gradient(90deg, #14b8a6, #0ea5e9)",
                animation: "shimmer 1.5s ease-in-out infinite",
                width: "40%",
              }}
            />
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div
          className="rounded-2xl p-8 text-center"
          style={{
            background:
              "linear-gradient(135deg, rgba(239, 68, 68, 0.08), rgba(220, 38, 38, 0.04))",
            border: "1px solid rgba(239, 68, 68, 0.2)",
          }}
        >
          <div className="text-4xl mb-3">⚠️</div>
          <p className="text-red-400 font-semibold mb-1">
            Failed to load forecast
          </p>
          <p className="text-red-300/70 text-sm max-w-md mx-auto">{error}</p>
        </div>
      )}

      {/* Results */}
      {data && !loading && (
        <>
          {/* Stats cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <div
              className="rounded-xl p-5"
              style={{
                background: "rgba(30, 41, 59, 0.5)",
                border: "1px solid rgba(148, 163, 184, 0.1)",
              }}
            >
              <p className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-1">
                Strategy
              </p>
              <p className="text-teal-400 font-semibold text-sm truncate">
                {data.strategy}
              </p>
            </div>
            <div
              className="rounded-xl p-5"
              style={{
                background: "rgba(30, 41, 59, 0.5)",
                border: "1px solid rgba(148, 163, 184, 0.1)",
              }}
            >
              <p className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-1">
                MAE
              </p>
              <p className="text-2xl font-bold gradient-text">{data.mae}</p>
            </div>
            <div
              className="rounded-xl p-5"
              style={{
                background: "rgba(30, 41, 59, 0.5)",
                border: "1px solid rgba(148, 163, 184, 0.1)",
              }}
            >
              <p className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-1">
                Total Predictions
              </p>
              <p className="text-2xl font-bold text-gray-100">
                {data.total_predictions.toLocaleString()}
              </p>
            </div>
          </div>

          {/* Table */}
          <div
            className="rounded-2xl overflow-hidden"
            style={{
              background: "rgba(30, 41, 59, 0.5)",
              border: "1px solid rgba(148, 163, 184, 0.1)",
            }}
          >
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr
                    style={{
                      background: "rgba(255, 255, 255, 0.03)",
                      borderBottom: "1px solid rgba(148, 163, 184, 0.1)",
                    }}
                  >
                    <th className="text-left text-gray-400 font-medium px-5 py-3">#</th>
                    <th className="text-left text-gray-400 font-medium px-5 py-3">Location</th>
                    <th className="text-left text-gray-400 font-medium px-5 py-3">Item ID</th>
                    <th className="text-right text-gray-400 font-medium px-5 py-3">Predicted Qty</th>
                    <th className="text-right text-gray-400 font-medium px-5 py-3">Actual Qty</th>
                    <th className="text-right text-gray-400 font-medium px-5 py-3">Avg Price</th>
                  </tr>
                </thead>
                <tbody>
                  {paginated.map((row: ForecastPrediction, idx: number) => (
                    <tr
                      key={`${row.location}-${row.item_id}`}
                      className="hover:bg-white/[0.02] transition-colors"
                      style={{
                        borderBottom: "1px solid rgba(148, 163, 184, 0.06)",
                      }}
                    >
                      <td className="px-5 py-3 text-gray-500">
                        {(page - 1) * PAGE_SIZE + idx + 1}
                      </td>
                      <td className="px-5 py-3 text-gray-300 font-medium">
                        {row.location}
                      </td>
                      <td className="px-5 py-3">
                        <code
                          className="text-xs px-2 py-0.5 rounded text-teal-300"
                          style={{
                            background: "rgba(20, 184, 166, 0.1)",
                            border: "1px solid rgba(20, 184, 166, 0.2)",
                          }}
                        >
                          {row.item_id}
                        </code>
                      </td>
                      <td className="px-5 py-3 text-right font-bold text-gray-100">
                        {row.quantity_predict}
                      </td>
                      <td className="px-5 py-3 text-right text-gray-400">
                        {row.actual_quantity}
                      </td>
                      <td className="px-5 py-3 text-right text-gray-400">
                        {formatPrice(row.avg_price)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-3 mt-8 mb-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-medium text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed hover:text-white transition-all"
                style={{
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(148, 163, 184, 0.12)",
                }}
              >
                ← Previous
              </button>
              <p className="text-sm text-gray-400">
                Page <span className="text-gray-200">{page}</span> of{" "}
                <span className="text-gray-200">{totalPages}</span>
              </p>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-medium text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed hover:text-white transition-all"
                style={{
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(148, 163, 184, 0.12)",
                }}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

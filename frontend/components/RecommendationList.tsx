"use client";

import Link from "next/link";

/**
 * RecommendationList — replaces the old manual item-ID input form.
 * Now shows a helpful message directing users to browse the catalog.
 */
export default function RecommendationList() {
  return (
    <div
      className="rounded-2xl p-8 sm:p-10 text-center"
      style={{
        background: "rgba(15, 23, 42, 0.6)",
        border: "1px solid rgba(148, 163, 184, 0.1)",
      }}
    >
      <div className="text-5xl mb-5">🛍️</div>
      <h2 className="text-xl font-bold text-gray-100 mb-3">
        How Recommendations Work
      </h2>
      <p className="text-gray-400 max-w-lg mx-auto mb-2 text-sm leading-relaxed">
        Browse our product catalog and click on any product to see its detail
        page. Recommendations are generated automatically based on the product
        you&apos;re viewing.
      </p>
      <ul className="text-gray-400 text-sm max-w-md mx-auto mb-6 text-left space-y-2">
        <li className="flex items-start gap-2">
          <span className="text-teal-400 mt-0.5">•</span>
          <span>
            <strong className="text-gray-200">All products</strong> show
            related items via co-purchase analysis (Solution&nbsp;1).
          </span>
        </li>
        <li className="flex items-start gap-2">
          <span className="text-teal-400 mt-0.5">•</span>
          <span>
            <strong className="text-gray-200">Diaper products</strong>{" "}
            additionally show up-sale recommendations (Solution&nbsp;2).
          </span>
        </li>
      </ul>
      <Link
        href="/"
        className="btn-gradient inline-flex items-center gap-2 px-6 py-2.5 text-sm"
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
            d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1"
          />
        </svg>
        Browse Products
      </Link>
    </div>
  );
}

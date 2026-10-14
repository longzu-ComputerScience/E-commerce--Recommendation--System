"use client";

import { useState } from "react";

interface SearchFilterProps {
  categories: string[];
  onFilterChange: (filters: { search: string; category: string }) => void;
}

export default function SearchFilter({
  categories,
  onFilterChange,
}: SearchFilterProps) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");

  const triggerSearch = () => {
    onFilterChange({ search, category });
  };

  const handleCategoryChange = (value: string) => {
    setCategory(value);
    onFilterChange({ search, category: value });
  };

  const handleClear = () => {
    setSearch("");
    setCategory("");
    onFilterChange({ search: "", category: "" });
  };

  const hasFilters = search !== "" || category !== "";

  return (
    <div
      className="glass-surface p-4 mb-8"
      style={{
        background: "rgba(30, 41, 59, 0.5)",
        border: "1px solid rgba(148, 163, 184, 0.1)",
      }}
    >
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <svg
            className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-teal-400/60"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="Search by category, brand, or item ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && triggerSearch()}
            className="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm transition-all placeholder:text-gray-500 text-gray-200 focus:outline-none"
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(148, 163, 184, 0.12)",
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "rgba(20, 184, 166, 0.5)";
              e.currentTarget.style.boxShadow =
                "0 0 12px rgba(20, 184, 166, 0.12)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "rgba(148, 163, 184, 0.12)";
              e.currentTarget.style.boxShadow = "none";
            }}
          />
        </div>
        <select
          value={category}
          onChange={(e) => handleCategoryChange(e.target.value)}
          className="px-4 py-2.5 rounded-lg text-sm transition-all cursor-pointer sm:w-52 text-gray-200 focus:outline-none"
          style={{
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(148, 163, 184, 0.12)",
          }}
        >
          <option value="">All Categories</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
        <button onClick={triggerSearch} className="btn-gradient px-6 py-2.5 text-sm">
          Search
        </button>
        {hasFilters && (
          <button
            onClick={handleClear}
            className="px-4 py-2.5 text-gray-400 hover:text-gray-200 rounded-lg hover:bg-white/5 transition-all text-sm"
            style={{ border: "1px solid rgba(148, 163, 184, 0.12)" }}
          >
            Clear
          </button>
        )}
      </div>
    </div>
  );
}

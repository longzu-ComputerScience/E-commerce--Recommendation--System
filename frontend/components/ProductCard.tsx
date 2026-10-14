import Link from "next/link";
import { Product } from "@/lib/types";

function formatPrice(price: number) {
  return new Intl.NumberFormat("vi-VN", {
    style: "currency",
    currency: "VND",
  }).format(price);
}

/** Hash-based gradient picker for card accents */
function getAccentGradient(category: string): string {
  const gradients = [
    "from-teal-500/20 to-cyan-500/10",
    "from-sky-500/20 to-blue-500/10",
    "from-emerald-500/20 to-teal-500/10",
    "from-amber-500/20 to-orange-500/10",
    "from-rose-500/20 to-pink-500/10",
    "from-cyan-500/20 to-sky-500/10",
    "from-violet-500/20 to-indigo-500/10",
    "from-lime-500/20 to-green-500/10",
  ];
  let hash = 0;
  for (let i = 0; i < category.length; i++) {
    hash = category.charCodeAt(i) + ((hash << 5) - hash);
  }
  return gradients[Math.abs(hash) % gradients.length];
}

const CATEGORY_ICONS: Record<string, string> = {
  Babycare: "\uD83D\uDC76",
  "Đồ chơi & Sách": "\uD83E\uDDE9",
  "Dinh dưỡng": "\uD83C\uDF7C",
  "Đồ dùng gia đình": "\uD83C\uDFE0",
  "Thời Trang": "\uD83D\uDC55",
  "Tã": "\uD83E\uDDF7",
};

function getCategoryIcon(category_l1: string): string {
  return CATEGORY_ICONS[category_l1] || "\uD83D\uDED2";
}

export default function ProductCard({ product }: { product: Product }) {
  const accentGradient = getAccentGradient(product.category_l1 || "");
  const icon = getCategoryIcon(product.category_l1);

  return (
    <Link href={`/products/${product.item_id}`} className="group block">
      <div
        className="relative h-full flex flex-col overflow-hidden transition-all duration-300 group-hover:-translate-y-1"
        style={{
          background: "rgba(30, 41, 59, 0.6)",
          backdropFilter: "blur(8px)",
          border: "1px solid rgba(148, 163, 184, 0.1)",
          borderRadius: "16px",
          padding: "16px",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "rgba(20, 184, 166, 0.4)";
          e.currentTarget.style.boxShadow =
            "0 0 20px rgba(20, 184, 166, 0.1), 0 8px 32px rgba(0,0,0,0.3)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "rgba(148, 163, 184, 0.1)";
          e.currentTarget.style.boxShadow = "none";
        }}
      >
        {/* Image area with gradient */}
        <div
          className={`bg-gradient-to-br ${accentGradient} rounded-xl h-36 flex items-center justify-center mb-3 relative overflow-hidden`}
        >
          <span className="text-4xl group-hover:scale-110 transition-transform duration-500 animate-float">
            {icon}
          </span>
          <div
            className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
            style={{
              background:
                "linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.05) 50%, transparent 60%)",
            }}
          />
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          {/* Category badge */}
          <span
            className="inline-block text-[10px] font-semibold px-2.5 py-0.5 rounded-full mb-1.5 w-fit truncate max-w-full"
            style={{
              background:
                "linear-gradient(135deg, rgba(20, 184, 166, 0.12), rgba(14, 165, 233, 0.12))",
              color: "#5eead4",
              border: "1px solid rgba(20, 184, 166, 0.2)",
            }}
          >
            {product.category_l1}
          </span>

          {/* Product name */}
          <h3 className="text-sm font-semibold text-gray-200 mb-1 line-clamp-2 leading-snug group-hover:text-teal-300 transition-colors duration-300">
            {product.category}
          </h3>

          {/* Brand */}
          <p className="text-xs text-gray-400 mb-3 truncate">
            {product.brand}
          </p>

          {/* Price */}
          <div
            className="mt-auto pt-2"
            style={{ borderTop: "1px solid rgba(148, 163, 184, 0.08)" }}
          >
            <p className="text-base font-bold gradient-text">
              {formatPrice(product.price)}
            </p>
          </div>
        </div>
      </div>
    </Link>
  );
}

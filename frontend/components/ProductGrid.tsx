import { Product } from "@/lib/types";
import ProductCard from "./ProductCard";

interface ProductGridProps {
  products: Product[];
  title?: string;
}

export default function ProductGrid({ products, title }: ProductGridProps) {
  if (products.length === 0) {
    return (
      <div className="text-center py-16 animate-fade-in-up">
        <div className="text-5xl mb-4 opacity-50 animate-float">📦</div>
        <p className="text-gray-300 text-lg font-medium">No products found</p>
        <p className="text-gray-500 text-sm mt-1">
          Try adjusting your search or filters
        </p>
      </div>
    );
  }

  return (
    <div>
      {title && (
        <h2 className="text-xl font-bold text-gray-200 mb-4">{title}</h2>
      )}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-5">
        {products.map((product, idx) => (
          <div
            key={product.item_id}
            className="animate-card-in"
            style={{ animationDelay: `${idx * 40}ms` }}
          >
            <ProductCard product={product} />
          </div>
        ))}
      </div>
    </div>
  );
}

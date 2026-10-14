export interface Product {
  item_id: string;
  price: number;
  category_l1: string;
  category_l2: string;
  category_l3: string;
  category: string;
  brand: string;
  manufacturer: string;
  sale_status: number;
  description?: string | null;
  raw_size?: string | null;
  normalized_size?: string | null;
  size_rank?: number | null;
  is_diaper?: boolean | null;
}

export interface ProductListResponse {
  products: Product[];
  total: number;
  page: number;
  page_size: number;
}

export interface RecommendationResponse {
  item_id: string;
  recommendations: (Product & {
    co_count?: number;
    behavior_score?: number;
    upsale_score?: number;
    final_score?: number;
  })[];
  strategy: string;
}

export interface RelatedProductsResponse {
  item_id: string;
  related: (Product & {
    co_count?: number;
    behavior_score?: number;
  })[];
  strategy: string;
}

export interface ForecastPrediction {
  location: number;
  item_id: string;
  quantity_predict: number;
  actual_quantity: number;
  avg_price: number;
}

export interface ForecastResponse {
  strategy: string;
  mae: number;
  total_predictions: number;
  predictions: ForecastPrediction[];
}

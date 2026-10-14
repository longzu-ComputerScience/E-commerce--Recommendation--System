import {
  Product,
  ProductListResponse,
  RecommendationResponse,
  RelatedProductsResponse,
  ForecastResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchAPI<T>(path: string, timeoutMs = 10000): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      signal: controller.signal,
    });
    if (!res.ok) {
      throw new Error(`API error: ${res.status} ${res.statusText}`);
    }
    return res.json();
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "Request timed out. The backend may be starting up — please try again."
      );
    }
    if (err instanceof TypeError) {
      throw new Error(
        "Cannot reach the backend at " +
          API_BASE +
          ". Make sure it is running and CORS is configured correctly."
      );
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export async function getProducts(
  params: {
    page?: number;
    page_size?: number;
    category?: string;
    brand?: string;
    search?: string;
  } = {}
): Promise<ProductListResponse> {
  const sp = new URLSearchParams();
  if (params.page) sp.set("page", String(params.page));
  if (params.page_size) sp.set("page_size", String(params.page_size));
  if (params.category) sp.set("category", params.category);
  if (params.brand) sp.set("brand", params.brand);
  if (params.search) sp.set("search", params.search);
  const qs = sp.toString();
  return fetchAPI<ProductListResponse>(`/products${qs ? `?${qs}` : ""}`);
}

export async function getProduct(itemId: string): Promise<Product> {
  return fetchAPI<Product>(`/products/${encodeURIComponent(itemId)}`);
}

export async function getRecommendations(
  itemId: string,
  n: number = 20
): Promise<RecommendationResponse> {
  return fetchAPI<RecommendationResponse>(
    `/recommendations/${encodeURIComponent(itemId)}?n=${n}`
  );
}

export async function getRelatedProducts(
  itemId: string,
  n: number = 20
): Promise<RelatedProductsResponse> {
  return fetchAPI<RelatedProductsResponse>(
    `/related/${encodeURIComponent(itemId)}?n=${n}`
  );
}

export async function getCategories(): Promise<string[]> {
  return fetchAPI<string[]>("/categories");
}

export async function getForecast(): Promise<ForecastResponse> {
  // Forecast training can be slow on first call — use 120s timeout
  return fetchAPI<ForecastResponse>("/forecast/solution3", 120000);
}

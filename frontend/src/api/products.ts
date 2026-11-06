import { apiClient } from "./client";
import type { Paginated, Product, SimilarResponse } from "../types";

export function fetchProducts(category?: string) {
  return apiClient.get<Paginated<Product>>("/products/", {
    params: category ? { category } : undefined,
  });
}

export function fetchProduct(id: number) {
  return apiClient.get<Product>(`/products/${id}/`);
}

export function createProduct(data: { name: string; description: string; category: string; price: string }) {
  return apiClient.post<Product>("/products/", data);
}

export function updateProduct(id: number, data: { name: string; description: string; category: string; price: string }) {
  return apiClient.put<Product>(`/products/${id}/`, data);
}

export function deleteProduct(id: number) {
  return apiClient.delete(`/products/${id}/`);
}

export function fetchSimilar(id: number, k = 5) {
  return apiClient.get<SimilarResponse>(`/products/${id}/similar/`, { params: { k } });
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
}

export interface Product {
  id: number;
  name: string;
  description: string;
  category: string;
  price: string;
  created_at: string;
  updated_at: string;
}

export interface SimilarProduct {
  product_id: number;
  name: string;
  price: string;
  score: number;
}

export interface SimilarResponse {
  similar: SimilarProduct[];
  blurb: string;
  stub_mode: boolean;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

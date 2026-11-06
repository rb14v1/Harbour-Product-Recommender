import { createBrowserRouter, Navigate } from "react-router-dom";

import { ProtectedRoute } from "../auth/ProtectedRoute";
import { ProductDetailPage } from "../features/products/ProductDetailPage";
import { ProductFormPage } from "../features/products/ProductFormPage";
import { ProductsListPage } from "../features/products/ProductsListPage";
import { AppLayout } from "../layouts/AppLayout";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "/", element: <ProductsListPage /> },
          { path: "/products/new", element: <ProductFormPage /> },
          { path: "/products/:id", element: <ProductDetailPage /> },
          { path: "/products/:id/edit", element: <ProductFormPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);

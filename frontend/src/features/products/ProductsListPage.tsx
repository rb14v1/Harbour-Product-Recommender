import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { deleteProduct, fetchProducts } from "../../api/products";
import { extractErrorMessage } from "../../api/client";
import type { Product } from "../../types";

export function ProductsListPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load(categoryFilter: string) {
    setLoading(true);
    setError(null);
    fetchProducts(categoryFilter || undefined)
      .then((res) => setProducts(res.data.results))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load(category);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleFilterSubmit(e: React.FormEvent) {
    e.preventDefault();
    load(category);
  }

  async function handleDelete(id: number) {
    if (!window.confirm("Delete this product?")) return;
    try {
      await deleteProduct(id);
      setProducts((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  const categories = Array.from(new Set(products.map((p) => p.category))).sort();

  return (
    <div>
      <div className="page-header">
        <h1>Products</h1>
        <Link to="/products/new"><button>Add Product</button></Link>
      </div>

      <form className="inline-form" onSubmit={handleFilterSubmit}>
        <label>
          Category
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
        <button type="submit">Filter</button>
      </form>

      {error && <div className="form-error">{error}</div>}
      {loading ? (
        <div className="page-loading">Loading...</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Price</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id}>
                <td><Link to={`/products/${product.id}`}>{product.name}</Link></td>
                <td>{product.category}</td>
                <td>${product.price}</td>
                <td className="actions">
                  <Link to={`/products/${product.id}/edit`}><button className="secondary">Edit</button></Link>
                  <button className="danger" onClick={() => handleDelete(product.id)}>Delete</button>
                </td>
              </tr>
            ))}
            {products.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">No products yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { extractErrorMessage } from "../../api/client";
import { fetchProduct, fetchSimilar } from "../../api/products";
import type { Product, SimilarResponse } from "../../types";

export function ProductDetailPage() {
  const { id } = useParams();
  const [product, setProduct] = useState<Product | null>(null);
  const [similar, setSimilar] = useState<SimilarResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    Promise.all([fetchProduct(Number(id)), fetchSimilar(Number(id), 5)])
      .then(([productRes, similarRes]) => {
        setProduct(productRes.data);
        setSimilar(similarRes.data);
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="page-loading">Loading...</div>;
  if (error) return <div className="form-error">{error}</div>;
  if (!product) return null;

  return (
    <div>
      <div className="page-header">
        <h1>{product.name}</h1>
        <Link to={`/products/${product.id}/edit`}><button className="secondary">Edit</button></Link>
      </div>

      <div className="card">
        <p className="muted">{product.category} &middot; ${product.price}</p>
        <p>{product.description}</p>
      </div>

      <div className="card">
        <h2>You May Also Like</h2>
        {similar?.stub_mode && (
          <p className="muted">
            Running in stub mode: no OPENAI_API_KEY is configured, so recommendations use
            deterministic placeholder embeddings/text instead of real AI output.
          </p>
        )}

        {similar && similar.similar.length === 0 && (
          <p className="muted">No other products to compare yet - add a few more products.</p>
        )}

        {similar && similar.similar.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Price</th>
                <th>Similarity score</th>
              </tr>
            </thead>
            <tbody>
              {similar.similar.map((item) => (
                <tr key={item.product_id}>
                  <td><Link to={`/products/${item.product_id}`}>{item.name}</Link></td>
                  <td>${item.price}</td>
                  <td>{item.score.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {similar && (
          <p style={{ marginTop: "1rem" }}><strong>Recommendation:</strong> {similar.blurb}</p>
        )}
      </div>
    </div>
  );
}

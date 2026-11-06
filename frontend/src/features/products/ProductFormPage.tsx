import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { extractErrorMessage } from "../../api/client";
import { createProduct, fetchProduct, updateProduct } from "../../api/products";

export function ProductFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [price, setPrice] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(isEdit);

  useEffect(() => {
    if (!id) return;
    fetchProduct(Number(id))
      .then((res) => {
        setName(res.data.name);
        setDescription(res.data.description);
        setCategory(res.data.category);
        setPrice(res.data.price);
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload = { name, description, category, price };
      if (isEdit) {
        await updateProduct(Number(id), payload);
      } else {
        await createProduct(payload);
      }
      navigate("/");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="page-loading">Loading...</div>;

  return (
    <div>
      <h1>{isEdit ? "Edit Product" : "Add Product"}</h1>
      <form className="card" onSubmit={handleSubmit} style={{ maxWidth: 480 }}>
        {error && <div className="form-error">{error}</div>}
        <div className="form-row">
          <label style={{ width: "100%" }}>
            Name
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
        </div>
        <div className="form-row">
          <label style={{ width: "100%" }}>
            Description
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              style={{ padding: "0.4rem 0.5rem", border: "1px solid #ccc", borderRadius: 4, fontSize: "0.9rem" }}
            />
          </label>
        </div>
        <div className="form-row">
          <label>
            Category
            <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. electronics" />
          </label>
          <label>
            Price
            <input type="number" step="0.01" min="0.01" value={price} onChange={(e) => setPrice(e.target.value)} required />
          </label>
        </div>
        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : isEdit ? "Save Changes" : "Create Product"}
        </button>
      </form>
    </div>
  );
}

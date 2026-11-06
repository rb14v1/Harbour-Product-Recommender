# Product Recommender

A small single-user-role product catalog with AI-powered "You May Also
Like" recommendations. React + Vite + TypeScript frontend, Django REST
Framework backend, PostgreSQL + pgvector for similarity search. No
Celery/Redis - there is no background work to run.

## AI / vector architecture

- **Embeddings** (`backend/apps/common/ai.py::get_embedding`) - real OpenAI
  embeddings (`text-embedding-3-large`, shortened to `EMBEDDING_DIMENSIONS`
  via the API's `dimensions` param) when `OPENAI_API_KEY` is set, otherwise
  a **deterministic stub**: a SHA-256 hash of the input text seeds a PRNG
  that produces an L2-normalized vector. The stub is reproducible (same
  text -> same vector, so it's fully testable) but **not semantically
  meaningful** - don't expect useful rankings from it. Real recommendation
  quality requires a real `OPENAI_API_KEY`.
- **Chat/blurb generation** (`generate_answer`) - real OpenAI chat
  completions (model from `OPENAI_CHAT_MODEL`, default `gpt-5.6-sol`) when
  a key is set, otherwise a templated stub string starting with
  `[STUB AI RESPONSE — set OPENAI_API_KEY for real output]`.
- **Storage** (`backend/apps/common/embedding_field.py`) - `Product.embedding`
  is a `pgvector.django.VectorField` on Postgres, or a plain `JSONField`
  (list of floats) on SQLite (`USE_SQLITE=True`, dev-only). Same attribute
  name either way, chosen by one factory function.
- **Search** (`backend/apps/common/vector_search.py::similarity_search`) -
  same function signature on both backends: pgvector's `CosineDistance` in
  `.order_by()` on Postgres, a pure-Python cosine-similarity sort on SQLite.
- The Postgres `vector` extension is created automatically by a `RunPython`
  guard in `apps/products/migrations/0001_initial.py` (no-op on SQLite).

This pattern is intentionally identical across every sibling AI app in this
workspace.

## Data model

- **User** - `AbstractUser` with `email` as `USERNAME_FIELD`. Single role.
- **Product** - `user`, `name`, `description`, `category` (free text),
  `price`, `embedding` (computed from `name + "\n" + description` on every
  save - see `Product.save()`), `created_at`/`updated_at`.

## REST API

- `POST /api/auth/register/`, `POST /api/auth/login/` (JWT),
  `POST /api/auth/refresh/`, `POST /api/auth/logout/`, `GET /api/auth/me/`
- `/api/products/` - list/create/retrieve/update/delete, `?category=`
- `GET /api/products/{id}/similar/?k=5` - the `k` nearest *other* products
  owned by the requesting user (self and other users' products are always
  excluded), plus a short AI-generated blurb:
  ```json
  {
    "similar": [{"product_id": 2, "name": "...", "price": "19.99", "score": 0.87}],
    "blurb": "...",
    "stub_mode": true
  }
  ```

Every queryset is scoped to `request.user` - there is no cross-user access
even by guessing another object's id (see
`apps/products/tests/test_products.py` for the isolation tests).

## Seed data

`apps/products/migrations/0002_seed_data.py` is an idempotent data
migration that creates a demo user (`demo@example.com` / `demo12345`) and
an 18-product catalog across 4 categories (electronics, home goods, outdoor
gear, books), computing each product's embedding at seed time via the same
`get_embedding()` used everywhere else. Re-running `migrate` never creates
duplicates.

## Running locally with Docker (Postgres + pgvector)

```bash
cp .env.example .env
docker compose up --build
```

Backend on http://localhost:8000, frontend on http://localhost:5173.
`docker-compose.yml` uses the `pgvector/pgvector:pg16` image, which already
has the extension installed.

## Running the backend without Docker (dev-only SQLite override)

No Postgres/pgvector/Docker needed for this:

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; venv\Scripts\activate.bat on cmd
pip install -r requirements.txt
export USE_SQLITE=True         # set USE_SQLITE=True on cmd / $env:USE_SQLITE="True" on PowerShell
python manage.py migrate
python manage.py test
python manage.py runserver
```

**Never set `USE_SQLITE=True` in docker-compose or production.** Leave
`OPENAI_API_KEY` unset to run entirely on the deterministic AI stub (no
network access or API cost needed); the frontend's product detail page
shows a "running in stub mode" note whenever it is.

## Running the frontend

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
npm run build   # production build
```

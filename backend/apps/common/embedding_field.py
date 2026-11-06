"""
Defines the embedding column type used by any model that stores an AI
embedding vector (currently just `apps.products.models.Product.embedding`).

- On Postgres (production / docker-compose), this is a genuine
  `pgvector.django.VectorField` of dimension `settings.EMBEDDING_DIMENSIONS`.
  Using it requires the `vector` Postgres extension to be installed
  (`CREATE EXTENSION vector;`) - see the RunPython guard in
  `apps/products/migrations/0001_initial.py`.
- On SQLite (dev-only, `USE_SQLITE=True` in the environment), pgvector isn't
  available at all, so the exact same attribute name is instead backed by a
  plain `JSONField` holding a list of floats. `apps.common.vector_search`
  hides this difference behind one function (`similarity_search`) so caller
  code (views, migrations, tests) never has to branch on which backend is
  active - only this module and `vector_search.py` know about it.

This pattern is intentionally identical across every sibling AI app in this
workspace for consistency.
"""
from django.conf import settings
from django.db import models


def EmbeddingField(**kwargs):
    """Factory returning the correct Django field instance for the active
    database backend. Always use this instead of importing VectorField or
    JSONField directly, so model code stays backend-agnostic."""
    kwargs.setdefault("null", True)
    kwargs.setdefault("blank", True)

    if settings.USE_SQLITE:
        return models.JSONField(**kwargs)

    # Imported lazily so the `pgvector` package is only required when
    # actually running against Postgres (it still needs to be installed per
    # requirements.txt either way, but this keeps the SQLite dev path from
    # depending on pgvector's C extension being importable/working).
    from pgvector.django import VectorField

    return VectorField(dimensions=settings.EMBEDDING_DIMENSIONS, **kwargs)

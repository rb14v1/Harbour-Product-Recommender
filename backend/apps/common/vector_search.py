"""
Backend-agnostic nearest-neighbour search over an EmbeddingField column.

similarity_search(queryset, query_vector, top_k, field_name='embedding')
returns the `top_k` objects in `queryset` most similar (by cosine
similarity) to `query_vector`, ordered nearest-first, with the computed
cosine similarity stashed on each returned object as `_similarity_score`
(a float in [-1, 1], higher is more similar).

- On Postgres, this uses pgvector's `CosineDistance` directly in
  `.order_by()`, so the database does the heavy lifting (and can use a
  pgvector index if one exists).
- On SQLite (dev-only, `USE_SQLITE=True`), there is no vector extension, so
  candidates are pulled into Python and cosine similarity is computed by
  hand, then sorted and sliced. This is fine for small dev/demo datasets and
  is NOT intended to scale - it exists purely so the whole
  embed -> store -> search pipeline is testable without Postgres/pgvector.

Same function signature either way, so calling code (views, tests) never
needs to know or care which backend is active.
"""
import math

from django.conf import settings


def _cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def similarity_search(queryset, query_vector, top_k, field_name="embedding"):
    if settings.USE_SQLITE:
        scored = []
        for obj in queryset:
            vector = getattr(obj, field_name)
            if not vector:
                continue
            score = _cosine_similarity(list(query_vector), list(vector))
            scored.append((score, obj))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = scored[:top_k]
        results = []
        for score, obj in top:
            obj._similarity_score = score
            results.append(obj)
        return results

    from pgvector.django import CosineDistance

    annotated = queryset.annotate(
        _distance=CosineDistance(field_name, list(query_vector))
    ).order_by("_distance")[:top_k]
    results = list(annotated)
    for obj in results:
        # pgvector's CosineDistance is 1 - cosine_similarity, so convert
        # back to a similarity score for a consistent return shape with the
        # SQLite branch above.
        obj._similarity_score = 1 - obj._distance
    return results

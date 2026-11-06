"""
AI layer: text embeddings + chat-style answer generation, with a
deterministic stub fallback so the whole pipeline (embed -> store -> search
-> explain) is fully testable with no OPENAI_API_KEY, no network access, and
no API cost.

*** STUB WARNING - READ BEFORE TRUSTING ANY "SIMILARITY" RESULT ***
When OPENAI_API_KEY is unset, `get_embedding()` returns a vector that is
deterministic (the same input text always produces the same output vector,
which is what makes it safe to unit test and to seed demo data with) but is
NOT semantically meaningful: it is derived from a SHA-256 hash of the input
text used to seed a PRNG, so it has no relationship whatsoever to the
real-world meaning of the text. Two products with very similar descriptions
will get essentially random stub vectors relative to each other. The
pipeline (storage, pgvector/SQLite search, ranking, API plumbing) is fully
exercised and correct either way, but do not expect the stub to produce
useful "You may also like" recommendations - real recommendation quality
requires a real OPENAI_API_KEY.
"""
import hashlib
import math
import random

from django.conf import settings


def get_embedding(text: str) -> list[float]:
    """Return an embedding vector of length settings.EMBEDDING_DIMENSIONS
    for `text`. Uses the real OpenAI embeddings API when OPENAI_API_KEY is
    configured, otherwise a deterministic stub - see module docstring."""
    if settings.OPENAI_API_KEY:
        from openai import OpenAI  # imported lazily: never required without a key

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )
        return response.data[0].embedding

    # --- deterministic stub (no OPENAI_API_KEY configured) ---
    seed = hashlib.sha256(text.encode("utf-8")).hexdigest()
    rng = random.Random(seed)
    vector = [rng.uniform(-1.0, 1.0) for _ in range(settings.EMBEDDING_DIMENSIONS)]

    # L2-normalize so stub vectors behave like real embeddings for cosine
    # similarity (unit length), even though direction is meaningless.
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector
    return [v / norm for v in vector]


def generate_answer(question: str, context_snippets: list[str]) -> str:
    """Return a short natural-language answer/blurb given `question` (e.g. a
    product name) and a list of context snippets (e.g. similar products'
    descriptions). Uses the real OpenAI chat completions API when
    OPENAI_API_KEY is configured, otherwise a deterministic templated stub -
    see module docstring."""
    if settings.OPENAI_API_KEY:
        from openai import OpenAI  # imported lazily: never required without a key

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        context_block = "\n".join(f"- {snippet}" for snippet in context_snippets) or "- (none)"
        response = client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful product recommendation assistant. "
                    "Write a short, friendly 1-2 sentence recommendation blurb.",
                },
                {
                    "role": "user",
                    "content": f"A shopper is viewing: {question}\n\n"
                    f"Similar products in their catalog:\n{context_block}",
                },
            ],
        )
        return response.choices[0].message.content

    # --- deterministic templated stub (no OPENAI_API_KEY configured) ---
    example = context_snippets[0][:200] if context_snippets else "none"
    return (
        f"[STUB AI RESPONSE — set OPENAI_API_KEY for real output] "
        f"{len(context_snippets)} similar product(s) found. Example: {example}"
    )

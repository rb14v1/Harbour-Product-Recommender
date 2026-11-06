from django.conf import settings
from django.db import models

from apps.common.embedding_field import EmbeddingField


class Product(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=100, blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # See apps/common/embedding_field.py: a pgvector VectorField on Postgres,
    # a plain JSONField (list of floats) on SQLite. Computed from
    # `name + "\n" + description` - see save() below and
    # embedding_source_text().
    embedding = EmbeddingField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def embedding_source_text(self) -> str:
        return f"{self.name}\n{self.description}"

    def save(self, *args, recompute_embedding=True, **kwargs):
        """Recomputes and stores the embedding on every create/update by
        default (per spec: "On Product create/update, compute and store
        embedding via get_embedding"). Pass recompute_embedding=False to
        skip this (e.g. when a caller - such as a test or the seed data
        migration - is setting `embedding` directly itself)."""
        if recompute_embedding:
            from apps.common.ai import get_embedding

            self.embedding = get_embedding(self.embedding_source_text())
        super().save(*args, **kwargs)

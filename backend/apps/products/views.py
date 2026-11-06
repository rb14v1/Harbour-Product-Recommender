from django.conf import settings
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.ai import generate_answer
from apps.common.vector_search import similarity_search
from apps.products.models import Product
from apps.products.serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """Everything here is scoped to request.user - get_queryset() is the
    only way objects are looked up (including for retrieve/update/delete/
    similar via DRF's get_object(), which calls get_queryset() under the
    hood), so a user can never read or act on another user's products even
    by guessing an id."""

    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Product.objects.filter(user=self.request.user)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__iexact=category)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        product = self.get_object()

        try:
            k = int(request.query_params.get("k", 5))
        except (TypeError, ValueError):
            k = 5
        k = max(1, min(k, 50))

        candidates = Product.objects.filter(user=request.user).exclude(pk=product.pk)
        top = similarity_search(candidates, product.embedding, k)

        similar_payload = [
            {
                "product_id": p.id,
                "name": p.name,
                "price": str(p.price),
                "score": round(float(p._similarity_score), 6),
            }
            for p in top
        ]
        blurb = generate_answer(product.name, [p.description for p in top])

        return Response({
            "similar": similar_payload,
            "blurb": blurb,
            "stub_mode": not bool(settings.OPENAI_API_KEY),
        })

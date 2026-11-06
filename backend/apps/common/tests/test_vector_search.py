from django.test import TestCase

from apps.accounts.models import User
from apps.common.test_utils import pad_vector
from apps.common.vector_search import similarity_search
from apps.products.models import Product


def _make_product(user, name, vector):
    """Creates a Product with an exact, known embedding (bypassing the real
    get_embedding() stub) so similarity ranking can be verified against
    hand-computed expected results."""
    product = Product(
        user=user,
        name=name,
        description="description",
        category="test",
        price="9.99",
        embedding=vector,
    )
    product.save(recompute_embedding=False)
    return product


class SimilaritySearchRankingTests(TestCase):
    """Constructs products with known embedding vectors and checks that
    similarity_search ranks nearest-first and correctly excludes products
    outside the given queryset (both self-exclusion and cross-user
    isolation are enforced by the caller filtering the queryset before it
    reaches similarity_search - these tests confirm that filtering is
    respected)."""

    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", password="StrongPass123!")
        self.other_user = User.objects.create_user(email="intruder@example.com", password="StrongPass123!")

        # query vector is [1, 0, 0] (padded to EMBEDDING_DIMENSIONS below —
        # real Postgres pgvector columns reject any other length)
        self.query_vector = pad_vector([1.0, 0.0, 0.0])

        self.source = _make_product(self.user, "source", pad_vector([1.0, 0.0, 0.0]))
        self.near = _make_product(self.user, "near", pad_vector([0.95, 0.05, 0.0]))          # cos ~0.9987
        self.mid = _make_product(self.user, "mid", pad_vector([0.7, 0.7, 0.0]))              # cos ~0.7071
        self.far = _make_product(self.user, "far", pad_vector([0.0, 1.0, 0.0]))              # cos = 0.0
        self.opposite = _make_product(self.user, "opposite", pad_vector([-1.0, 0.0, 0.0]))   # cos = -1.0
        self.other_users_product = _make_product(self.other_user, "other-users-near", pad_vector([0.99, 0.01, 0.0]))

    def test_ranks_nearest_first_and_excludes_self(self):
        candidates = Product.objects.filter(user=self.user).exclude(pk=self.source.pk)
        results = similarity_search(candidates, self.query_vector, top_k=10)

        names = [p.name for p in results]
        self.assertEqual(names, ["near", "mid", "far", "opposite"])
        self.assertNotIn("source", names)

        # scores strictly decrease
        scores = [p._similarity_score for p in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_top_k_slices_correctly(self):
        candidates = Product.objects.filter(user=self.user).exclude(pk=self.source.pk)
        results = similarity_search(candidates, self.query_vector, top_k=2)
        self.assertEqual([p.name for p in results], ["near", "mid"])

    def test_cross_user_isolation(self):
        """A caller that (correctly) scopes its candidate queryset to one
        user never sees another user's products in the results, even if
        that other user's product would otherwise rank highly."""
        candidates = Product.objects.filter(user=self.user).exclude(pk=self.source.pk)
        results = similarity_search(candidates, self.query_vector, top_k=10)
        self.assertNotIn(self.other_users_product.id, [p.id for p in results])

    def test_similarity_score_values(self):
        candidates = Product.objects.filter(user=self.user).exclude(pk=self.source.pk)
        results = similarity_search(candidates, self.query_vector, top_k=10)
        by_name = {p.name: p._similarity_score for p in results}
        self.assertAlmostEqual(by_name["far"], 0.0, places=6)
        self.assertAlmostEqual(by_name["opposite"], -1.0, places=6)
        self.assertGreater(by_name["near"], by_name["mid"])

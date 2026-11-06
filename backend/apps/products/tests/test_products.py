from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.products.models import Product

DEMO_EMAIL = "demo@example.com"


class ProductAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", password="StrongPass123!")
        self.other_user = User.objects.create_user(email="intruder@example.com", password="StrongPass123!")
        self.client.force_authenticate(user=self.user)

        self.p1 = Product.objects.create(
            user=self.user,
            name="Wireless Mouse",
            description="An ergonomic wireless mouse with long battery life.",
            category="electronics",
            price="29.99",
        )
        self.p2 = Product.objects.create(
            user=self.user,
            name="Mechanical Keyboard",
            description="A tactile mechanical keyboard for productivity and gaming.",
            category="electronics",
            price="89.99",
        )
        self.p3 = Product.objects.create(
            user=self.user,
            name="Yoga Mat",
            description="A non-slip yoga mat for home workouts.",
            category="home goods",
            price="19.99",
        )
        self.other_product = Product.objects.create(
            user=self.other_user,
            name="Secret Gadget",
            description="Not visible to any other user.",
            category="electronics",
            price="999.99",
        )

    def test_embedding_computed_on_create(self):
        self.assertIsNotNone(self.p1.embedding)
        self.assertEqual(len(self.p1.embedding), settings.EMBEDDING_DIMENSIONS)

    def test_embedding_recomputed_on_update(self):
        original = list(self.p1.embedding)
        self.p1.name = "Wireless Mouse Pro"
        self.p1.save()
        self.p1.refresh_from_db()
        # pgvector-django returns VectorField values as numpy arrays on
        # Postgres (vs plain lists from SQLite's JSONField fallback);
        # comparing an array directly raises "ambiguous truth value" under
        # assertNotEqual, so cast to list first to compare on either backend.
        self.assertNotEqual(original, list(self.p1.embedding))

    def test_products_list_scoped_to_user(self):
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [p["name"] for p in response.data["results"]]
        self.assertIn("Wireless Mouse", names)
        self.assertNotIn("Secret Gadget", names)

    def test_category_filter(self):
        response = self.client.get(reverse("product-list"), {"category": "electronics"})
        names = {p["name"] for p in response.data["results"]}
        self.assertEqual(names, {"Wireless Mouse", "Mechanical Keyboard"})

    def test_create_requires_positive_price(self):
        response = self.client.post(reverse("product-list"), {
            "name": "Broken Product",
            "description": "desc",
            "category": "electronics",
            "price": "-5.00",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_similar_endpoint_excludes_self_and_cross_user(self):
        url = reverse("product-similar", kwargs={"pk": self.p1.pk})
        response = self.client.get(url, {"k": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["product_id"] for item in response.data["similar"]]
        self.assertNotIn(self.p1.id, ids)
        self.assertNotIn(self.other_product.id, ids)
        # only this user's two other products can possibly appear
        self.assertLessEqual(len(ids), 2)
        self.assertTrue(set(ids).issubset({self.p2.id, self.p3.id}))

    def test_similar_endpoint_blurb_stub_format(self):
        url = reverse("product-similar", kwargs={"pk": self.p1.pk})
        response = self.client.get(url)
        self.assertTrue(response.data["blurb"].startswith("[STUB AI RESPONSE"))
        self.assertTrue(response.data["stub_mode"])

    def test_similar_endpoint_response_shape(self):
        url = reverse("product-similar", kwargs={"pk": self.p1.pk})
        response = self.client.get(url)
        self.assertIn("similar", response.data)
        self.assertIn("blurb", response.data)
        for item in response.data["similar"]:
            self.assertIn("product_id", item)
            self.assertIn("name", item)
            self.assertIn("price", item)
            self.assertIn("score", item)

    def test_cannot_retrieve_other_users_product(self):
        url = reverse("product-detail", kwargs={"pk": self.other_product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_get_similar_for_other_users_product(self):
        url = reverse("product-similar", kwargs={"pk": self.other_product.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_update_other_users_product(self):
        url = reverse("product-detail", kwargs={"pk": self.other_product.pk})
        response = self.client.patch(url, {"name": "Hijacked"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_request_rejected(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SeedDataMigrationTests(APITestCase):
    """Confirms the apps/products/migrations/0002_seed_data.py RunPython
    migration seeded the demo user and catalog as part of building the test
    database (Django's test runner applies all migrations, including data
    migrations, when creating the test DB)."""

    def test_demo_user_created(self):
        demo = User.objects.filter(email=DEMO_EMAIL).first()
        self.assertIsNotNone(demo)
        self.assertTrue(demo.check_password("demo12345"))

    def test_demo_products_seeded_with_embeddings(self):
        demo = User.objects.get(email=DEMO_EMAIL)
        products = Product.objects.filter(user=demo)
        self.assertGreaterEqual(products.count(), 15)
        self.assertLessEqual(products.count(), 18)

        categories = set(products.values_list("category", flat=True))
        self.assertGreaterEqual(len(categories), 3)

        for product in products:
            self.assertIsNotNone(product.embedding)
            self.assertEqual(len(product.embedding), settings.EMBEDDING_DIMENSIONS)

    def test_seed_migration_is_idempotent_on_rerun(self):
        """Re-running the seed function directly (simulating a second
        `migrate`) must not create duplicate rows. Imported via importlib
        since the migration module's filename starts with a digit and
        can't be used in a normal `import` statement."""
        import importlib

        from django.apps import apps as django_apps

        seed_module = importlib.import_module("apps.products.migrations.0002_seed_data")

        before = Product.objects.filter(user__email=DEMO_EMAIL).count()
        seed_module.seed_demo_data(django_apps, None)
        after = Product.objects.filter(user__email=DEMO_EMAIL).count()
        self.assertEqual(before, after)

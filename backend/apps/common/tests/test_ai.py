import math

from django.conf import settings
from django.test import TestCase

from apps.common.ai import generate_answer, get_embedding


class GetEmbeddingStubTests(TestCase):
    """OPENAI_API_KEY is unset in the test environment, so these exercise
    the deterministic stub path in apps.common.ai.get_embedding."""

    def test_stub_used_when_no_api_key(self):
        self.assertEqual(settings.OPENAI_API_KEY, "")

    def test_deterministic_same_text_same_vector(self):
        a = get_embedding("Wireless Mouse\nAn ergonomic wireless mouse.")
        b = get_embedding("Wireless Mouse\nAn ergonomic wireless mouse.")
        self.assertEqual(a, b)

    def test_different_text_different_vector(self):
        a = get_embedding("Wireless Mouse")
        b = get_embedding("Mechanical Keyboard")
        self.assertNotEqual(a, b)

    def test_correct_dimensionality(self):
        vector = get_embedding("some product text")
        self.assertEqual(len(vector), settings.EMBEDDING_DIMENSIONS)

    def test_l2_normalized(self):
        vector = get_embedding("some product text")
        norm = math.sqrt(sum(v * v for v in vector))
        self.assertAlmostEqual(norm, 1.0, places=6)

    def test_values_in_expected_range(self):
        vector = get_embedding("some product text")
        self.assertTrue(all(-1.0 <= v <= 1.0 for v in vector))


class GenerateAnswerStubTests(TestCase):
    def test_stub_format_with_context(self):
        answer = generate_answer("Wireless Mouse", ["A great mouse.", "Another product."])
        self.assertTrue(answer.startswith("[STUB AI RESPONSE"))
        self.assertIn("2 similar product(s) found", answer)
        self.assertIn("A great mouse.", answer)

    def test_stub_format_with_no_context(self):
        answer = generate_answer("Wireless Mouse", [])
        self.assertTrue(answer.startswith("[STUB AI RESPONSE"))
        self.assertIn("0 similar product(s) found", answer)
        self.assertIn("Example: none", answer)

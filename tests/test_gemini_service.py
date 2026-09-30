import unittest

from services.gemini_service import GeminiService


class GeminiServiceModelFallbackTests(unittest.TestCase):
    def test_default_model_is_supported(self):
        self.assertEqual(GeminiService("test-key").model, "gemini-2.5-flash")


if __name__ == "__main__":
    unittest.main()

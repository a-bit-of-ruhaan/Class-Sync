import os
import unittest

from backend.config import resolve_api_key


class TestAIConfig(unittest.TestCase):
    def test_resolve_api_key_prefers_gemini_key(self):
        original = os.environ.get("GEMINI_API_KEY")
        google_original = os.environ.get("GOOGLE_API_KEY")
        try:
            os.environ["GEMINI_API_KEY"] = "gemini-key"
            os.environ["GOOGLE_API_KEY"] = "google-key"
            self.assertEqual(resolve_api_key(), "gemini-key")
        finally:
            if original is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = original

            if google_original is None:
                os.environ.pop("GOOGLE_API_KEY", None)
            else:
                os.environ["GOOGLE_API_KEY"] = google_original

    def test_resolve_api_key_uses_google_alias(self):
        original = os.environ.get("GEMINI_API_KEY")
        google_original = os.environ.get("GOOGLE_API_KEY")
        try:
            os.environ.pop("GEMINI_API_KEY", None)
            os.environ["GOOGLE_API_KEY"] = "google-key"
            self.assertEqual(resolve_api_key(), "google-key")
        finally:
            if original is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = original

            if google_original is None:
                os.environ.pop("GOOGLE_API_KEY", None)
            else:
                os.environ["GOOGLE_API_KEY"] = google_original


if __name__ == "__main__":
    unittest.main()

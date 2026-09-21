import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


FEATURE_API_KEYS = {
    "summarizer": ("SUMMARIZER_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"),
    "quiz": ("QUIZ_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"),
    "facts": ("FACTS_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"),
}


def resolve_api_key(*, preferred_keys=None, feature=None):
    """Return the first configured API key for the supported providers.

    The app is currently implemented with the Google Gemini SDK, but some older
    setup docs still mention OpenAI. This helper accepts either provider name so
    the runtime configuration is resilient and the error message is explicit.
    """
    if preferred_keys is None:
        preferred_keys = FEATURE_API_KEYS.get(
            feature,
            ("GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"),
        )

    for key_name in preferred_keys:
        value = os.getenv(key_name)
        if value and value.strip():
            return value.strip()

    joined = ", ".join(preferred_keys)
    raise RuntimeError(
        f"No API key found. Set one of: {joined}. "
        "Add it to your .env file in the project root."
    )

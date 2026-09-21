import json
import re
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

from backend.config import resolve_api_key

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MODEL_NAME = "gemini-2.5-flash"

# Structure for Gemini's response
class FactList(BaseModel):
    facts: List[str]


def _parse_fact_list_response(response):
    """Accept Gemini structured responses in either parsed or text form."""
    if response is None:
        raise ValueError("Gemini returned no response for fact generation.")

    parsed = getattr(response, "parsed", None)
    if parsed is not None:
        if isinstance(parsed, FactList):
            return parsed
        if isinstance(parsed, dict):
            return FactList.model_validate(parsed)

    text = getattr(response, "text", "") or ""
    cleaned_text = text.strip()
    if cleaned_text.startswith("```"):
        cleaned_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned_text, flags=re.IGNORECASE | re.DOTALL)

    if not cleaned_text:
        raise ValueError("Gemini returned an empty fact payload.")

    try:
        return FactList.model_validate_json(cleaned_text)
    except Exception:
        try:
            return FactList.model_validate(json.loads(cleaned_text))
        except Exception as exc:
            raise ValueError(f"Gemini returned an invalid fact payload: {cleaned_text[:200]}") from exc


def generate_random_facts():
    """
    Generates exactly 4 random interesting facts using Gemini.
    Returns a list containing 4 strings.
    """

    prompt = """
    Generate exactly 4 interesting and surprising random facts.

    Rules:
    - Return exactly 4 facts.
    - Each fact should be 1-2 sentences maximum.
    - Make the facts interesting and easy to understand.
    - Try to use different topics for each fact.
    - Facts should be factual and not fictional.
    - Avoid opinions and speculation.
    """

    api_key = resolve_api_key()

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FactList,
            temperature=1.0,
        ),
    )

    result = _parse_fact_list_response(response)

    if len(result.facts) != 4:
        raise ValueError("Gemini did not return exactly 4 facts.")

    return result.facts
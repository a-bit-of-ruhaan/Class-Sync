from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Structure for Gemini's response
class FactList(BaseModel):
    facts: List[str]


# Create Gemini client
# Make sure GEMINI_API_KEY is set in your environment
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


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

    response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FactList,
            temperature=1.0,
        ),
    )

    result = FactList.model_validate_json(response.text)

    if len(result.facts) != 4:
        raise ValueError("Gemini did not return exactly 4 facts.")

    return result.facts
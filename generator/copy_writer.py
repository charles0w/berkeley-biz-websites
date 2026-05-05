"""Generate tagline + about copy for a business using Claude Haiku."""

import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "scraper", ".env"))


def generate_copy(business: dict) -> dict:
    """
    Given a business dict from the DB, return {"tagline": str, "about": str}.
    Uses claude-haiku-4-5 — fast and cheap (~$0.001 per business).
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    types_str = ", ".join(json.loads(business.get("types", "[]"))[:3]).replace("_", " ")
    rating_str = f"{business['rating']}/5 ({business['ratings_count']} reviews)" if business.get("rating") else "new"

    prompt = f"""Write website copy for a local business. Be warm, genuine, and specific — no corporate speak.

Business name: {business["name"]}
Type: {types_str}
Location: {business.get("address", "Berkeley, CA")}
Rating: {rating_str}

Return ONLY valid JSON with exactly these two keys:
{{
  "tagline": "A compelling tagline under 10 words. Warm, specific to this type of business.",
  "about": "2-3 sentences. Tell the story of a neighborhood business that locals love. Mention Berkeley if natural. Sound human, not AI-generated."
}}"""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = msg.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

"""
Generate tagline + about paragraph for a business using Claude Haiku.
"""
from __future__ import annotations
import os
import anthropic

_client: anthropic.Anthropic | None = None

CATEGORY_HINTS = {
    'cafe': 'coffee shop or cafe',
    'salon': 'hair salon',
    'beauty': 'beauty salon or nail spa',
    'food': 'restaurant or eatery',
    'fitness': 'gym or fitness studio',
    'retail': 'retail store',
    'services': 'local service business',
}

SYSTEM = """\
You write website copy for small, locally-owned Berkeley businesses.
Rules you never break:
- No emojis anywhere.
- No exclamation marks.
- No AI-cliche words: Elevate, Seamless, Experience, Journey, Crafted, Artisan, Vibrant, Discover, Transform, Unlock, Navigate, Leverage.
- No hollow compliments ("amazing", "passionate team").
- Write like a local who knows the place — specific, grounded, understated.
- Tagline: 10-15 words max. Present tense. No period.
- About: 2-3 sentences. Facts + texture. No made-up specifics."""


def _client_instance() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    return _client


def generate_copy(business: dict) -> dict:
    name = business['name']
    category_hint = CATEGORY_HINTS.get(business.get('category', ''), 'local business')
    address = business.get('address', '')
    rating = business.get('rating', 0)
    review_count = business.get('review_count', 0)

    prompt = f"""Business: {name}
Type: {category_hint}
Address: {address}
Rating: {rating} stars from {review_count} Google reviews

Write:
TAGLINE: [10-15 word caption — what this place actually is, not what it aspires to be]
ABOUT: [2-3 sentences — neighborhood context, what the place is like, why people go]"""

    msg = _client_instance().messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=350,
        system=SYSTEM,
        messages=[{'role': 'user', 'content': prompt}],
    )

    text = msg.content[0].text.strip()
    tagline, about = '', ''

    for line in text.splitlines():
        if line.startswith('TAGLINE:'):
            tagline = line.removeprefix('TAGLINE:').strip().rstrip('.')
        elif line.startswith('ABOUT:'):
            about = line.removeprefix('ABOUT:').strip()

    return {
        'tagline': tagline or f"A Berkeley {category_hint}",
        'about': about or '',
    }

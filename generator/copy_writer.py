"""
Generate tagline, about paragraph, and services list for a business using Claude Haiku.
"""
from __future__ import annotations
import os
import anthropic

_client: anthropic.Anthropic | None = None

CATEGORY_HINTS = {
    'cafe': 'coffee shop or cafe',
    'salon': 'hair salon',
    'beauty': 'beauty salon or nail spa',
    'nail': 'nail salon',
    'food': 'restaurant or eatery',
    'restaurant': 'restaurant',
    'fitness': 'gym or fitness studio',
    'retail': 'retail store',
    'services': 'local service business',
}

# Typical services for each category — used if Haiku output fails to parse
FALLBACK_SERVICES: dict[str, list[dict]] = {
    'cafe':       [{'name': 'Drip Coffee', 'price': '$4'}, {'name': 'Latte', 'price': '$6'}, {'name': 'Cappuccino', 'price': '$5'}, {'name': 'Cold Brew', 'price': '$6'}, {'name': 'Pastry', 'price': '$4'}],
    'food':       [{'name': 'Lunch Special', 'price': '$14'}, {'name': 'Dinner Entree', 'price': '$22'}, {'name': 'Appetizer', 'price': '$12'}, {'name': 'Dessert', 'price': '$9'}, {'name': 'Drinks', 'price': '$6'}],
    'restaurant': [{'name': 'Starter', 'price': '$13'}, {'name': 'Main Course', 'price': '$24'}, {'name': 'Dessert', 'price': '$10'}, {'name': 'Wine by Glass', 'price': '$14'}, {'name': 'Cocktail', 'price': '$16'}],
    'salon':      [{'name': "Women's Cut", 'price': '$65'}, {'name': "Men's Cut", 'price': '$40'}, {'name': 'Blowout', 'price': '$55'}, {'name': 'Color', 'price': '$120'}, {'name': 'Highlights', 'price': '$150'}],
    'beauty':     [{'name': 'Classic Manicure', 'price': '$30'}, {'name': 'Gel Manicure', 'price': '$45'}, {'name': 'Classic Pedicure', 'price': '$40'}, {'name': 'Gel Pedicure', 'price': '$55'}, {'name': 'Mani + Pedi', 'price': '$70'}],
    'nail':       [{'name': 'Classic Manicure', 'price': '$30'}, {'name': 'Gel Manicure', 'price': '$45'}, {'name': 'Classic Pedicure', 'price': '$40'}, {'name': 'Gel Pedicure', 'price': '$55'}, {'name': 'Nail Art', 'price': '$15+'}],
    'fitness':    [{'name': 'Drop-in Class', 'price': '$25'}, {'name': 'Monthly Membership', 'price': '$89'}, {'name': '10-Class Pack', 'price': '$199'}, {'name': 'Personal Training', 'price': '$95'}, {'name': 'Annual Membership', 'price': '$799'}],
    'retail':     [{'name': 'Browse In-Store', 'price': 'Free'}, {'name': 'Gift Wrapping', 'price': '$5'}, {'name': 'Special Orders', 'price': 'Varies'}, {'name': 'Store Credit', 'price': 'Available'}, {'name': 'Loyalty Program', 'price': 'Free'}],
    'services':   [{'name': 'Consultation', 'price': 'Free'}, {'name': 'Basic Service', 'price': '$75'}, {'name': 'Standard Package', 'price': '$149'}, {'name': 'Premium Package', 'price': '$249'}, {'name': 'Custom Quote', 'price': 'Contact us'}],
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
- About: 2-3 sentences. Facts + texture. No made-up specifics.
- IMPORTANT: The ABOUT must NOT begin by repeating or paraphrasing the TAGLINE. Start with a completely different angle.
- Services: 5-6 realistic offerings with typical Berkeley prices for this business type. Format: Name|$Price (no descriptions, no ranges unless unavoidable).
- Output format must be exactly three lines with no markdown, no bold, no asterisks:
  TAGLINE: [your tagline]
  ABOUT: [your about text]
  SERVICES: Name|$Price, Name|$Price, Name|$Price, Name|$Price, Name|$Price"""


def _client_instance() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    return _client


def _parse_services(raw: str) -> list[dict]:
    services = []
    for item in raw.split(','):
        parts = item.strip().split('|')
        if len(parts) == 2:
            name = parts[0].strip().strip('*_`')
            price = parts[1].strip().strip('*_`')
            if name and price:
                services.append({'name': name, 'price': price})
    return services[:6]


def generate_copy(business: dict) -> dict:
    name = business['name']
    category = business.get('category', 'services')
    category_hint = CATEGORY_HINTS.get(category, 'local business')
    address = business.get('address', '')
    rating = business.get('rating', 0)
    review_count = business.get('review_count', 0)

    prompt = f"""Business: {name}
Type: {category_hint}
Address: {address}
Rating: {rating} stars from {review_count} Google reviews

Write:
TAGLINE: [10-15 word caption — what this place actually is, not what it aspires to be]
ABOUT: [2-3 sentences — neighborhood context, what the place is like, why people go]
SERVICES: [5-6 realistic {category_hint} offerings with typical Berkeley prices]"""

    msg = _client_instance().messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=450,
        system=SYSTEM,
        messages=[{'role': 'user', 'content': prompt}],
    )

    text = msg.content[0].text.strip()
    tagline, about, services_raw = '', '', ''

    for line in text.splitlines():
        clean = line.strip().lstrip('*').lstrip('_').lstrip('#').strip()
        upper = clean.upper()
        if upper.startswith('TAGLINE:'):
            tagline = clean[8:].strip().strip('*_`').rstrip('.')
        elif upper.startswith('ABOUT:'):
            about = clean[6:].strip().strip('*_`')
        elif upper.startswith('SERVICES:'):
            services_raw = clean[9:].strip()

    # Fallback: salvage tagline from first parseable line
    if not tagline:
        lines = [l.strip().lstrip('*_#').strip() for l in text.splitlines() if l.strip()]
        for line in lines:
            if 10 < len(line) < 120 and not line.upper().startswith(('ABOUT', 'SERVICES')):
                tagline = line.rstrip('.')
                break

    # Fallback: about from lines after tagline
    if not about:
        found_tag = False
        parts = []
        for line in text.splitlines():
            clean = line.strip().lstrip('*_#').strip()
            if clean.upper().startswith('TAGLINE:'):
                found_tag = True
                continue
            if found_tag and clean and not clean.upper().startswith(('ABOUT:', 'SERVICES:')):
                parts.append(clean)
        if parts:
            about = ' '.join(parts)

    services = _parse_services(services_raw) if services_raw else []
    if not services:
        services = FALLBACK_SERVICES.get(category, FALLBACK_SERVICES['services'])

    return {
        'tagline': tagline or f'A local {category_hint} in Berkeley',
        'about': about or '',
        'services': services,
    }

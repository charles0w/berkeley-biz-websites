"""
Scrape local businesses near UC Berkeley that have no real owned website.
Saves results to data/businesses.db.

Usage:
    cd scraper && python scrape.py
"""
import os
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
import googlemaps
from dotenv import load_dotenv
from db import Database

_CEOS_URL = os.environ.get("CEOS_DASHBOARD_URL", "https://ceos-enterprise.vercel.app")

def _report(state: str, summary: str, ok: bool = True) -> None:
    secret = os.environ.get("CEOS_REPORT_SECRET", "").strip()
    if not secret:
        return
    try:
        payload = json.dumps({
            "agentId": "growth",
            "status": {"state": state, "lastRun": datetime.now(timezone.utc).isoformat(),
                       "summary": summary[:280], "ok": ok},
        }).encode()
        req = urllib.request.Request(
            f"{_CEOS_URL.rstrip('/')}/api/report", data=payload,
            headers={"x-report-secret": secret, "content-type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[ceo_report] {e}")

load_dotenv()

BERKELEY_LAT = 37.8716
BERKELEY_LNG = -122.2727
RADIUS_M = 2000

TYPES_TO_SCRAPE = [
    'restaurant', 'cafe', 'hair_care', 'beauty_salon', 'nail_salon',
    'bar', 'bakery', 'clothing_store', 'florist', 'spa',
    'shoe_store', 'jewelry_store', 'pet_store', 'gym', 'book_store',
]

PLACEHOLDER_DOMAINS = {
    # Listing / review sites
    'yelp.com', 'tripadvisor.com', 'foursquare.com',
    'yellowpages.com', 'whitepages.com', 'biz.yelp.com',
    # Social / link-in-bio
    'facebook.com', 'instagram.com', 'linktree.com', 'linktr.ee',
    # Delivery
    'grubhub.com', 'doordash.com', 'ubereats.com',
    # Booking / scheduling platforms (not owned sites)
    'edan.io', 'fresha.com', 'vagaro.com', 'booksy.com',
    'schedulicity.com', 'mindbodyonline.com', 'styleseat.com',
    # Google
    'sites.google.com', 'maps.google.com', 'business.google.com',
    # Generic drag-and-drop builders (no real brand presence)
    'square.site', 'squareup.com',
    'wix.com', 'wixsite.com',
    'squarespace.com',
    'godaddysites.com', 'godaddy.com/website',
    'weebly.com',
    'strikingly.com',
    'jimdo.com',
    'yolasite.com',
}



_DETAIL_FIELDS = ','.join([
    'name', 'formatted_address', 'formatted_phone_number',
    'website', 'opening_hours', 'rating', 'user_ratings_total', 'geometry',
])


def place_detail(api_key: str, place_id: str) -> dict:
    """Direct HTTP call to Places Details API — avoids the googlemaps library
    injecting deprecated 'photos'/'types' field names into every request."""
    qs = urllib.parse.urlencode({'place_id': place_id, 'fields': _DETAIL_FIELDS, 'key': 'REDACTED'})
    print(f'[debug] detail call: {qs}', flush=True)
    qs = urllib.parse.urlencode({'place_id': place_id, 'fields': _DETAIL_FIELDS, 'key': api_key})
    url = 'https://maps.googleapis.com/maps/api/place/details/json?' + qs
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read())
    if data.get('status') not in ('OK', 'ZERO_RESULTS'):
        raise RuntimeError(data.get('error_message') or data.get('status', 'unknown error'))
    return data.get('result', {})


def is_placeholder(url: str) -> bool:
    if not url:
        return True
    return any(d in url for d in PLACEHOLDER_DOMAINS)


def classify_category(types: list[str]) -> str:
    if any(t in types for t in ('cafe', 'coffee_shop')):
        return 'cafe'
    if any(t in types for t in ('hair_care', 'hair_salon')):
        return 'salon'
    if any(t in types for t in ('beauty_salon', 'nail_salon', 'spa')):
        return 'beauty'
    if any(t in types for t in ('gym', 'health', 'fitness_center')):
        return 'fitness'
    if any(t in types for t in ('clothing_store', 'shoe_store', 'jewelry_store', 'book_store', 'pet_store', 'florist')):
        return 'retail'
    if any(t in types for t in ('restaurant', 'food', 'bar', 'bakery', 'meal_takeaway')):
        return 'food'
    return 'services'


def parse_hours(opening_hours: dict) -> dict:
    if not opening_hours:
        return {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    result = {}
    for i, text in enumerate(opening_hours.get('weekday_text', [])):
        if i < len(days):
            parts = text.split(': ', 1)
            result[days[i]] = parts[1] if len(parts) > 1 else text
    return result


def scrape():
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        sys.exit('GOOGLE_MAPS_API_KEY not set — copy scraper/.env.example to scraper/.env and fill it in.')

    gmaps = googlemaps.Client(key=api_key)
    db = Database()
    total_new = 0

    for place_type in TYPES_TO_SCRAPE:
        print(f'\nScraping type: {place_type}')
        next_page_token = None

        for page in range(3):
            kwargs: dict = {
                'location': (BERKELEY_LAT, BERKELEY_LNG),
                'radius': RADIUS_M,
                'type': place_type,
            }
            if next_page_token:
                kwargs['page_token'] = next_page_token
                time.sleep(2.5)

            try:
                response = gmaps.places_nearby(**kwargs)
            except Exception as e:
                print(f'  API error: {e}')
                break

            print(f'  status={response.get("status")} results={len(response.get("results", []))}', flush=True)
            for place in response.get('results', []):
                place_id = place['place_id']

                try:
                    detail = place_detail(api_key, place_id)
                except Exception as e:
                    print(f'  detail error for {place.get("name")}: {e}')
                    continue

                website = detail.get('website', '')
                if not is_placeholder(website):
                    continue  # has a real owned site — skip

                hours = parse_hours(detail.get('opening_hours', {}))
                # types and photos come from the nearby result (not detail)
                # to avoid the invalid field names issue with the Places API.
                photo_refs = [p['photo_reference'] for p in place.get('photos', [])[:6]]

                db.upsert_business({
                    'place_id': place_id,
                    'name': detail['name'],
                    'address': detail.get('formatted_address', ''),
                    'phone': detail.get('formatted_phone_number', ''),
                    'website': website,
                    'rating': detail.get('rating', 0),
                    'review_count': detail.get('user_ratings_total', 0),
                    'category': classify_category(place.get('types', [])),
                    'hours_json': json.dumps(hours),
                    'photo_refs': json.dumps(photo_refs),
                    'lat': detail['geometry']['location']['lat'],
                    'lng': detail['geometry']['location']['lng'],
                })
                total_new += 1
                print(f'  + {detail["name"]} ({detail.get("rating", "?")}★, {detail.get("user_ratings_total", 0)} reviews)')

                time.sleep(0.15)

            next_page_token = response.get('next_page_token')
            if not next_page_token:
                break

    total = db.count()
    print(f'\nDone. {total_new} businesses saved/updated. Total in DB: {total}')
    return total_new, total


def run():
    """Run the scrape and report status to the CEO dashboard.

    Re-raises on failure so the GH Actions job is marked failed too — the
    error report is best-effort and fires before the re-raise.

    Skips silently (exit 0, no report) when GOOGLE_MAPS_API_KEY isn't set,
    so the daily cron stays green until the secret is added rather than
    spamming failures.
    """
    if not os.environ.get('GOOGLE_MAPS_API_KEY'):
        print('GOOGLE_MAPS_API_KEY not set — skipping scrape. '
              'Add it as a repo secret to activate the cron.')
        return None

    started = time.monotonic()
    try:
        total_new, total = scrape()
    except Exception as exc:
        _report(
            "error",
            f"scrape failed: {type(exc).__name__}: {str(exc).splitlines()[0][:120]}",
            ok=False,
        )
        raise
    _report("ok", f"{total_new} new/updated, {total} businesses in DB")
    return total_new, total


if __name__ == '__main__':
    run()

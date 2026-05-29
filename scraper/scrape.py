"""
Scrape local businesses near UC Berkeley that have no website.
Results are saved to data/businesses.db.

Usage:
    python scrape.py                          # scrape all default types, 1500m radius
    python scrape.py --radius 2000            # wider area
    python scrape.py --types restaurant,cafe  # specific types only
"""

import argparse
import logging
import os
import time

import requests
from dotenv import load_dotenv

from db import count_businesses, init_db, is_scraped, save_business

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

UC_BERKELEY = {"lat": 37.8719, "lng": -122.2585}

DEFAULT_TYPES = [
    "restaurant",
    "cafe",
    "bakery",
    "bar",
    "beauty_salon",
    "hair_care",
    "nail_salon",
    "clothing_store",
    "book_store",
    "shoe_store",
    "florist",
    "gym",
    "laundry",
]

BASE_URL = "https://places.googleapis.com/v1/places"

SEARCH_FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.location",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "places.businessStatus",
    "places.photos",
    "places.regularOpeningHours",
    "places.types",
])

DETAIL_FIELD_MASK = ",".join([
    "id",
    "displayName",
    "formattedAddress",
    "nationalPhoneNumber",
    "location",
    "websiteUri",
    "rating",
    "userRatingCount",
    "businessStatus",
    "photos",
    "regularOpeningHours",
    "types",
])


def _headers(api_key: str, field_mask: str = "") -> dict:
    h = {"X-Goog-Api-Key": api_key, "Content-Type": "application/json"}
    if field_mask:
        h["X-Goog-FieldMask"] = field_mask
    return h


def _normalize(place: dict) -> dict:
    """Convert Places API v1 field names to the format save_business() expects."""
    loc = place.get("location", {})
    photos_raw = place.get("photos", [])
    hours = place.get("regularOpeningHours", {}).get("weekdayDescriptions", [])

    return {
        "place_id": place.get("id"),
        "name": place.get("displayName", {}).get("text"),
        "formatted_address": place.get("formattedAddress"),
        "formatted_phone_number": place.get("nationalPhoneNumber"),
        "geometry": {"location": {"lat": loc.get("latitude"), "lng": loc.get("longitude")}},
        "website": place.get("websiteUri"),
        "rating": place.get("rating"),
        "user_ratings_total": place.get("userRatingCount"),
        "business_status": place.get("businessStatus"),
        "types": place.get("types", []),
        # Store the full resource name (e.g. "places/PLACE_ID/photos/PHOTO_ID")
        # generate.py reads this to build the v1 photo media URL
        "photos": [{"photo_reference": p["name"]} for p in photos_raw[:10]],
        "opening_hours": {"weekday_text": hours},
    }


def fetch_details(api_key: str, place_id: str) -> dict:
    resp = requests.get(
        f"{BASE_URL}/{place_id}",
        headers=_headers(api_key, DETAIL_FIELD_MASK),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def scrape_type(api_key: str, business_type: str, location: dict, radius: int) -> list[str]:
    """Scrape one business type. Returns names of no-website businesses saved."""
    saved = []
    payload = {
        "includedTypes": [business_type],
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": location["lat"], "longitude": location["lng"]},
                "radius": float(radius),
            }
        },
    }

    while True:
        resp = requests.post(
            f"{BASE_URL}:searchNearby",
            json=payload,
            headers=_headers(api_key, SEARCH_FIELD_MASK),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        for place in data.get("places", []):
            place_id = place.get("id")
            if not place_id:
                continue

            if is_scraped(place_id):
                log.debug("  skip (already in db): %s", place.get("displayName", {}).get("text"))
                continue

            time.sleep(0.05)

            try:
                details_raw = fetch_details(api_key, place_id)
            except Exception as e:
                log.warning("  could not fetch details for %s: %s", place_id, e)
                continue

            details = _normalize(details_raw)

            if details.get("business_status") == "CLOSED_PERMANENTLY":
                continue

            if not details.get("website"):
                save_business(details)
                name = details.get("name", place_id)
                saved.append(name)
                log.info("  [+] %s  |  %s", name, details.get("formatted_address", ""))
            else:
                log.debug("  [-] %s — has website", details.get("name"))

        next_token = data.get("nextPageToken")
        if not next_token:
            break

        log.debug("  fetching next page…")
        time.sleep(2)
        payload["pageToken"] = next_token

    return saved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--radius", type=int, default=1500, help="Search radius in metres (default 1500 ≈ 1 mile)")
    parser.add_argument("--types", type=str, default="", help="Comma-separated place types to scrape")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: GOOGLE_MAPS_API_KEY not set in scraper/.env")

    init_db()

    types_to_scrape = [t.strip() for t in args.types.split(",") if t.strip()] or DEFAULT_TYPES

    total_new = 0
    for btype in types_to_scrape:
        log.info("Scraping type: %s", btype)
        found = scrape_type(api_key, btype, UC_BERKELEY, args.radius)
        log.info("  → %d new businesses without websites", len(found))
        total_new += len(found)

    log.info("")
    log.info("Done. New businesses found this run: %d", total_new)
    log.info("Total in database: %d", count_businesses())
    log.info("Run `python generate.py` from the generator/ folder to build sites.")


if __name__ == "__main__":
    main()

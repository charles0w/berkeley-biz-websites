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

import googlemaps
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

# Only fetch the fields we actually use — keeps cost down
DETAIL_FIELDS = [
    "place_id",
    "name",
    "formatted_address",
    "formatted_phone_number",
    "geometry",
    "website",
    "rating",
    "user_ratings_total",
    "photo",
    "type",
    "opening_hours",
    "business_status",
]


def fetch_details(gmaps: googlemaps.Client, place_id: str) -> dict:
    resp = gmaps.place(place_id=place_id, fields=DETAIL_FIELDS)
    return resp.get("result", {})


def scrape_type(gmaps: googlemaps.Client, business_type: str, location: dict, radius: int) -> list[str]:
    """Scrape one business type. Returns names of no-website businesses saved."""
    saved = []
    resp = gmaps.places_nearby(location=location, radius=radius, type=business_type)

    while True:
        for place in resp.get("results", []):
            place_id = place["place_id"]

            if is_scraped(place_id):
                log.debug("  skip (already in db): %s", place.get("name"))
                continue

            time.sleep(0.05)  # gentle rate limiting
            details = fetch_details(gmaps, place_id)

            if details.get("business_status") == "CLOSED_PERMANENTLY":
                continue

            if not details.get("website"):
                save_business(details)
                name = details.get("name", place_id)
                saved.append(name)
                log.info("  [+] %s  |  %s", name, details.get("formatted_address", ""))
            else:
                log.debug("  [-] %s — has website", details.get("name"))

        next_token = resp.get("next_page_token")
        if not next_token:
            break

        log.debug("  fetching next page…")
        time.sleep(2)  # Places API requires a short delay before next_page_token works
        resp = gmaps.places_nearby(page_token=next_token)

    return saved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--radius", type=int, default=1500, help="Search radius in metres (default 1500 ≈ 1 mile)")
    parser.add_argument("--types", type=str, default="", help="Comma-separated place types to scrape")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: GOOGLE_MAPS_API_KEY not set in scraper/.env")

    gmaps = googlemaps.Client(key=api_key)
    init_db()

    types_to_scrape = [t.strip() for t in args.types.split(",") if t.strip()] or DEFAULT_TYPES

    total_new = 0
    for btype in types_to_scrape:
        log.info("Scraping type: %s", btype)
        found = scrape_type(gmaps, btype, UC_BERKELEY, args.radius)
        log.info("  → %d new businesses without websites", len(found))
        total_new += len(found)

    log.info("")
    log.info("Done. New businesses found this run: %d", total_new)
    log.info("Total in database: %d", count_businesses())
    log.info("Run `python generate.py` from the generator/ folder to build sites.")


if __name__ == "__main__":
    main()

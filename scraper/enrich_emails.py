"""
Find and store owner contact emails for businesses that are site_built=1 but have no email.

Sources tried in order per business:
  1. DuckDuckGo HTML search  → "{name} Berkeley CA email contact"
  2. Yelp business page      → scraped for mailto: links

Usage:
    python enrich_emails.py --list         # show businesses needing emails
    python enrich_emails.py --run          # enrich all, update DB
    python enrich_emails.py --run --dry    # enrich all, print only (no DB writes)
    python enrich_emails.py --one PLACE_ID # single business
"""

import argparse
import re
import sys
import time
import os

import requests
from urllib.parse import quote_plus

sys.path.insert(0, os.path.dirname(__file__))
from db import _conn

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

JUNK_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "squarespace.com",
    "wordpress.com", "shopify.com", "godaddy.com", "yelp.com",
    "google.com", "gmail.com", "facebook.com", "instagram.com",
    "apple.com", "icloud.com", "yahoo.com", "hotmail.com",  # too generic to attribute
    "w3.org", "schema.org", "openstreetmap.org",
}


def _clean_emails(raw: list[str]) -> list[str]:
    out = []
    for e in raw:
        e = e.lower().strip(".,;:\"'>")
        domain = e.split("@")[-1]
        if domain not in JUNK_DOMAINS and len(e) <= 80:
            out.append(e)
    return list(dict.fromkeys(out))  # deduplicate, preserve order


def search_ddg(name: str, address: str) -> list[str]:
    city = "Berkeley CA"
    q = f'"{name}" {city} email contact'
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(q)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        return _clean_emails(EMAIL_RE.findall(r.text))
    except Exception:
        return []


def search_yelp(name: str) -> list[str]:
    q = quote_plus(f"{name} Berkeley CA")
    url = f"https://www.yelp.com/search?find_desc={q}&find_loc=Berkeley%2C+CA"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        # Find the first yelp business link in results
        biz_urls = re.findall(r'href="(/biz/[^"?]+)', r.text)
        if not biz_urls:
            return []
        biz_url = "https://www.yelp.com" + biz_urls[0]
        time.sleep(1)
        r2 = requests.get(biz_url, headers=HEADERS, timeout=10)
        return _clean_emails(EMAIL_RE.findall(r2.text))
    except Exception:
        return []


def enrich_one(business: dict, dry: bool = False) -> str | None:
    name = business["name"]
    address = business.get("address", "")
    print(f"  [{name}]")

    emails: list[str] = []

    # Source 1: DuckDuckGo
    ddg = search_ddg(name, address)
    if ddg:
        print(f"    DDG:  {ddg}")
        emails.extend(ddg)
    time.sleep(1.5)

    # Source 2: Yelp (only if DDG found nothing)
    if not emails:
        yelp = search_yelp(name)
        if yelp:
            print(f"    Yelp: {yelp}")
            emails.extend(yelp)
        time.sleep(1.5)

    best = _clean_emails(emails)[0] if emails else None

    if best:
        print(f"    → {best}")
        if not dry:
            with _conn() as c:
                c.execute("UPDATE businesses SET email = ? WHERE place_id = ?", (best, business["place_id"]))
    else:
        print(f"    → not found")

    return best


def get_needs_email() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM businesses WHERE site_built = 1 AND (email IS NULL OR email = '') ORDER BY rating DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="Show businesses needing emails")
    ap.add_argument("--run", action="store_true", help="Enrich emails for all businesses needing one")
    ap.add_argument("--dry", action="store_true", help="Print results without writing to DB")
    ap.add_argument("--one", metavar="PLACE_ID", help="Enrich a single business by place_id")
    args = ap.parse_args()

    if args.list:
        businesses = get_needs_email()
        print(f"\n{len(businesses)} businesses need email enrichment:\n")
        for b in businesses:
            phone = b.get("phone") or "no phone"
            print(f"  {b['name']:<40}  {phone}")
        return

    if args.one:
        with _conn() as c:
            row = c.execute("SELECT * FROM businesses WHERE place_id = ?", (args.one,)).fetchone()
        if not row:
            print(f"place_id not found: {args.one}")
            sys.exit(1)
        enrich_one(dict(row), dry=args.dry)
        return

    if args.run:
        businesses = get_needs_email()
        print(f"\nEnriching {len(businesses)} businesses…\n")
        found = 0
        for b in businesses:
            result = enrich_one(b, dry=args.dry)
            if result:
                found += 1
        print(f"\nDone. Found emails for {found}/{len(businesses)} businesses.")
        return

    ap.print_help()


if __name__ == "__main__":
    main()

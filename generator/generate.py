"""
Generate and deploy a website for a business from the database.

Usage:
    python generate.py                    # list all businesses ready for site generation
    python generate.py <place_id>         # generate + deploy one site
    python generate.py all                # generate + deploy all without sites (careful: costs API + Vercel)
"""

import json
import os
import shutil
import subprocess
import sys

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scraper"))
from db import get_business, get_businesses_without_site, mark_site_built
from copy_writer import generate_copy

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "scraper", ".env"))

TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "site-template"))
GENERATED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generated"))
GMAPS_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")


def download_photos(photo_refs: list[str], output_dir: str) -> dict:
    """Download up to 5 photos from Places Photo API into output_dir/images/."""
    images_dir = os.path.join(output_dir, "public", "images")
    os.makedirs(images_dir, exist_ok=True)
    downloaded: list[str] = []

    for i, ref in enumerate(photo_refs[:5]):
        url = (
            f"https://maps.googleapis.com/maps/api/place/photo"
            f"?maxwidth=1600&photo_reference={ref}&key={GMAPS_KEY}"
        )
        try:
            resp = requests.get(url, allow_redirects=True, timeout=10)
            if resp.status_code == 200:
                filename = f"photo_{i}.jpg"
                with open(os.path.join(images_dir, filename), "wb") as f:
                    f.write(resp.content)
                downloaded.append(f"/images/{filename}")
                print(f"    photo {i+1}/{len(photo_refs[:5])} downloaded")
        except Exception as e:
            print(f"    WARNING: could not download photo {i}: {e}")

    return {
        "hero": downloaded[0] if downloaded else "/images/placeholder.jpg",
        "gallery": downloaded[1:4] if len(downloaded) > 1 else [],
    }


def build_business_json(business: dict, copy: dict, photos: dict) -> dict:
    raw_types = json.loads(business.get("types", "[]"))
    category = raw_types[0].replace("_", " ").title() if raw_types else "Local Business"

    return {
        "place_id": business["place_id"],
        "name": business["name"],
        "tagline": copy["tagline"],
        "about": copy["about"],
        "category": category,
        "address": business.get("address") or "",
        "phone": business.get("phone") or "",
        "hours_raw": json.loads(business.get("hours") or "[]"),
        "rating": business.get("rating") or 0,
        "photos": photos,
        "google_maps_url": f"https://www.google.com/maps/place/?q=place_id:{business['place_id']}",
        "accent_color": "#C8963C",
    }


def _vercel_name(site_dir: str) -> str:
    """Derive a valid Vercel project name from the site directory name (the place_id)."""
    import re
    name = os.path.basename(site_dir).lower()
    name = re.sub(r"[^a-z0-9._-]", "-", name)
    name = re.sub(r"-{3,}", "--", name)
    return name[:100]


def deploy_to_vercel(site_dir: str) -> str | None:
    """Run `vercel --prod` and return the deployment URL."""
    name = _vercel_name(site_dir)
    result = subprocess.run(
        f"npx vercel --yes --prod --name {name}",
        cwd=site_dir,
        capture_output=True,
        text=True,
        shell=True,
    )
    if result.returncode != 0:
        print("  Vercel error:\n", result.stderr)
        return None

    combined = result.stdout + "\n" + result.stderr
    for line in combined.splitlines():
        if "Production:" in line and "https://" in line:
            for token in line.split():
                if token.startswith("https://"):
                    return token.rstrip("]").strip()
    return None


def generate_site(place_id: str) -> str | None:
    business = get_business(place_id)
    if not business:
        raise SystemExit(f"No business with place_id={place_id} in the database.")

    print(f"\nGenerating site for: {business['name']}")

    # 1. Copy template (skip node_modules — Vercel installs them during cloud build)
    site_dir = os.path.join(GENERATED_DIR, place_id)
    if os.path.exists(site_dir):
        shutil.rmtree(site_dir)
    shutil.copytree(TEMPLATE_DIR, site_dir, ignore=shutil.ignore_patterns("node_modules", ".next"))

    # 2. Download photos
    print("  Downloading photos…")
    photo_refs = json.loads(business.get("photo_refs") or "[]")
    photos = download_photos(photo_refs, site_dir)

    # 3. Generate copy
    print("  Generating copy with Claude Haiku…")
    copy = generate_copy(business)
    print(f"    tagline: {copy['tagline']}")

    # 4. Write business.json
    biz_data = build_business_json(business, copy, photos)
    with open(os.path.join(site_dir, "business.json"), "w") as f:
        json.dump(biz_data, f, indent=2)

    # 5. Deploy
    print("  Deploying to Vercel…")
    url = deploy_to_vercel(site_dir)

    if url:
        mark_site_built(place_id, url)
        print(f"  Live at: {url}")
    else:
        print("  Deployed but could not parse URL — check Vercel dashboard.")

    return url


def main() -> None:
    if len(sys.argv) < 2:
        businesses = get_businesses_without_site()
        if not businesses:
            print("No businesses without sites in the database. Run scraper first.")
            return
        print(f"\n{len(businesses)} businesses ready for site generation:\n")
        for i, b in enumerate(businesses, 1):
            rating = f"{b['rating']}/5" if b.get("rating") else "no rating"
            print(f"  {i:>3}. {b['name']} ({rating})")
            print(f"       {b.get('address', '')}")
            print(f"       place_id: {b['place_id']}\n")
        print("Usage:")
        print("  python generate.py <place_id>    # generate one site")
        print("  python generate.py all           # generate all (watch your budget!)")

    elif sys.argv[1] == "all":
        for b in get_businesses_without_site():
            try:
                generate_site(b["place_id"])
            except Exception as e:
                print(f"  ERROR generating {b['name']}: {e}")

    else:
        generate_site(sys.argv[1])


if __name__ == "__main__":
    main()

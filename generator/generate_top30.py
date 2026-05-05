"""Generate and deploy sites for the top 30 businesses by rating."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scraper"))
from db import get_businesses_without_site
from generate import generate_site

businesses = get_businesses_without_site()[:29]  # already sorted by rating DESC; nono's is done

print(f"Generating {len(businesses)} sites...\n")
for i, b in enumerate(businesses, 1):
    print(f"[{i}/{len(businesses)}] {b['name']} (rating: {b.get('rating', 'N/A')})")
    try:
        url = generate_site(b["place_id"])
        if url:
            print(f"  OK: {url}\n")
        else:
            print("  WARNING: deployed but URL not parsed — check Vercel dashboard\n")
    except Exception as e:
        print(f"  ERROR: {e}\n")
    time.sleep(1)

print("Done.")

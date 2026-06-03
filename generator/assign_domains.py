"""
Batch-assign custom subdomains to all already-deployed Vercel projects.

Run AFTER adding *.charlesbuilds.online → cname.vercel-dns.com in Namecheap DNS.

Usage:
    cd generator
    python assign_domains.py              # assign all with demo_url
    python assign_domains.py --dry-run    # preview without calling API
"""
from __future__ import annotations
import os
import sys
import time
import argparse

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'scraper', '.env'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scraper'))

from db import Database
from generate import assign_custom_domain, CUSTOM_DOMAIN_BASE


def run(dry_run: bool = False):
    db = Database()
    rows = [b for b in db.get_all() if b.get('demo_url') and b.get('slug')]

    print(f'Assigning *.{CUSTOM_DOMAIN_BASE} subdomains to {len(rows)} sites...\n')

    ok = 0
    for i, biz in enumerate(rows):
        slug = biz['slug']
        expected = f'https://{slug}.{CUSTOM_DOMAIN_BASE}'

        # Skip if already using custom domain
        if biz.get('demo_url', '').startswith(f'https://{slug}.'):
            print(f'[{i+1}/{len(rows)}] {biz["name"][:35]} — already set')
            ok += 1
            continue

        print(f'[{i+1}/{len(rows)}] {biz["name"][:35]} → {slug}.{CUSTOM_DOMAIN_BASE}')

        if not dry_run:
            custom_url = assign_custom_domain(slug)
            if custom_url:
                db.update_business(biz['place_id'], demo_url=custom_url)
                ok += 1
                print(f'  ✓ {custom_url}')
            else:
                print(f'  ✗ failed')
            time.sleep(0.3)  # be polite to Vercel API
        else:
            print(f'  [dry run] would set: {expected}')
            ok += 1

    print(f'\nDone. {ok}/{len(rows)} subdomains {"previewed" if dry_run else "assigned"}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    run(dry_run=args.dry_run)

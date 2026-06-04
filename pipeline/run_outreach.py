"""
Daily outreach sender — sends v1 to businesses that have:
  - A demo site (demo_url set)
  - An email address (owner_email set)
  - Not yet been contacted (outreach_status = 'new')

Capped at MAX_PER_DAY to avoid spam flags and Resend rate limits.

Usage:
    cd pipeline
    python run_outreach.py --dry-run
    python run_outreach.py
"""
import os
import sys
import json
import argparse
import urllib.request
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'scraper', '.env'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scraper'))
from db import Database

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'outreach'))
import mailer as outreach_email

MAX_PER_DAY = 15
_CEOS_URL = os.environ.get('CEOS_DASHBOARD_URL', 'https://ceos-enterprise.vercel.app')


def _report(state: str, summary: str, ok: bool = True) -> None:
    secret = os.environ.get('CEOS_REPORT_SECRET', '').strip()
    if not secret:
        return
    try:
        payload = json.dumps({
            'agentId': 'growth',
            'status': {
                'state': state,
                'lastRun': datetime.now(timezone.utc).isoformat(),
                'summary': summary[:280],
                'ok': ok,
            },
        }).encode()
        req = urllib.request.Request(
            f"{_CEOS_URL.rstrip('/')}/api/report",
            data=payload,
            headers={'x-report-secret': secret, 'content-type': 'application/json'},
            method='POST',
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f'[ceo_report] {e}')


def find_ready(db: Database) -> list[dict]:
    """Businesses with demo + email that haven't been contacted yet."""
    rows = db.get_all()
    ready = [
        b for b in rows
        if b.get('demo_url')
        and b.get('owner_email')
        and b.get('outreach_status') in (None, 'new')
    ]
    # Highest-rated first — better leads get priority
    ready.sort(key=lambda b: (b.get('rating') or 0, b.get('review_count') or 0), reverse=True)
    return ready[:MAX_PER_DAY]


def run(dry_run: bool = False):
    db = Database()
    candidates = find_ready(db)

    if not candidates:
        print('No ready leads today (need demo_url + owner_email + outreach_status=new).')
        return 0

    print(f'{"[DRY RUN] " if dry_run else ""}Sending v1 to {len(candidates)} leads...\n')

    sent = 0
    for biz in candidates:
        print(f'  {biz["name"]} — {biz["owner_email"]} ({biz.get("rating", "?")}★)')
        if not dry_run:
            try:
                outreach_email.send(biz['place_id'], version='v1')
                sent += 1
            except Exception as e:
                print(f'    error: {e}')
        else:
            sent += 1

    if not dry_run:
        all_rows = db.get_all()
        total = len(all_rows)
        sites = sum(1 for b in all_rows if b.get('demo_url'))
        emailed = sum(1 for b in all_rows if b.get('outreach_status') not in (None, 'new'))
        replied = sum(1 for b in all_rows if b.get('outreach_replied_at'))
        closed = sum(1 for b in all_rows if b.get('closed_amount'))
        summary = (
            f'{total} scraped · {sites} sites · '
            f'{emailed} emailed · {replied} replies · {closed} closed'
        )
        _report('ok', summary)

    print(f'\nDone. {sent} emails {"(dry run)" if dry_run else "sent"}.')
    return sent


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    run(dry_run=args.dry_run)

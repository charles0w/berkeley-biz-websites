"""
Batch site generator — generates and deploys demo sites for all scraped businesses.

Processes all businesses with status='scraped' (or status='error' for retries).
Skips businesses that already have a demo_url.

Usage:
    cd generator
    python batch_generate.py                  # generate all pending
    python batch_generate.py --limit 10       # cap at 10 per run
    python batch_generate.py --retry-errors   # also retry status='error' rows
    python batch_generate.py --dry-run        # build only, do not deploy

Required env vars (scraper/.env or GitHub secrets):
    GOOGLE_MAPS_API_KEY
    ANTHROPIC_API_KEY
    VERCEL_TOKEN
    DATABASE_URL
"""
import os
import sys
import time
import argparse
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'scraper', '.env'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scraper'))

from db import Database
from generate import generate_site

_CEOS_URL = os.environ.get('CEOS_DASHBOARD_URL', 'https://ceos-enterprise.vercel.app')
_DELAY_BETWEEN_DEPLOYS_S = 5  # be polite to Vercel


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


def run(limit: int | None = None, retry_errors: bool = False, dry_run: bool = False):
    db = Database()
    all_rows = db.get_all()

    pending = [
        b for b in all_rows
        if not b.get('demo_url') and (
            b.get('status') == 'scraped'
            or (retry_errors and b.get('status') == 'error')
        )
    ]

    if limit:
        pending = pending[:limit]

    total = len(pending)
    if total == 0:
        print('No pending businesses. All scraped businesses already have demo sites.')
        _report('ok', _summary_line(db))
        return

    print(f'Generating sites for {total} businesses{"(dry run)" if dry_run else ""}...\n')

    done = 0
    failed = 0
    for i, biz in enumerate(pending):
        place_id = biz['place_id']
        name = biz['name']
        print(f'[{i+1}/{total}] {name}')
        try:
            generate_site(place_id, build_only=dry_run)
            done += 1
            print(f'  ✓ done')
        except Exception as e:
            failed += 1
            print(f'  ✗ failed: {e}')
            if not dry_run:
                db.update_business(place_id, status='error', notes=str(e)[:500])
        if i < total - 1:
            time.sleep(_DELAY_BETWEEN_DEPLOYS_S)

    summary = _summary_line(db)
    print(f'\nBatch complete. {done} succeeded, {failed} failed.')
    print(f'Dashboard summary: {summary}')

    state = 'ok' if failed == 0 else ('warn' if done > 0 else 'error')
    _report(state, summary, ok=(failed == 0))


def _summary_line(db: Database) -> str:
    rows = db.get_all()
    total = len(rows)
    generated = sum(1 for b in rows if b.get('demo_url'))
    emails_sent = sum(1 for b in rows if b.get('outreach_status') not in (None, 'new'))
    replied = sum(1 for b in rows if b.get('outreach_replied_at'))
    closed = sum(1 for b in rows if b.get('closed_amount'))
    return (
        f'{total} bizs scraped · {generated} sites built · '
        f'{emails_sent} emails sent · {replied} replies · {closed} closed'
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None, help='Max businesses to process')
    parser.add_argument('--retry-errors', action='store_true', help='Also retry status=error rows')
    parser.add_argument('--dry-run', action='store_true', help='Build only, do not deploy to Vercel')
    args = parser.parse_args()
    run(limit=args.limit, retry_errors=args.retry_errors, dry_run=args.dry_run)

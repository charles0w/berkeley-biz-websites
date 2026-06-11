"""
Automated follow-up sender.

Rules:
  v1 → sent, no reply after V2_DELAY_DAYS  → send v2
  v2 → sent, no reply after V3_DELAY_DAYS  → send v3
  v3 → sent                                 → no further follow-up

Respects opt-outs: skips any row with outreach_status='unsubscribed'.
Rate-limited: sends at most MAX_PER_RUN per execution to avoid spam flags.

Usage:
    cd pipeline
    python followup.py --dry-run     # preview what would be sent
    python followup.py               # send follow-ups
"""
import os
import sys
import json
import argparse
import urllib.request
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'scraper', '.env'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scraper'))
from db import Database

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'outreach'))
import mailer as outreach_email

V2_DELAY_DAYS = 7
V3_DELAY_DAYS = 7
MAX_PER_RUN = 15

_CEOS_URL = os.environ.get('CEOS_DASHBOARD_URL', 'https://ceos-enterprise.vercel.app')


def _report(state: str, summary: str, ok: bool = True,
            metrics: list[dict] | None = None) -> None:
    # NOTE: growth must never send profit= to the dashboard — closed_amount
    # already funds The Garage straight from the businesses table; reporting
    # it again would double-count.
    secret = os.environ.get('CEOS_REPORT_SECRET', '').strip()
    if not secret:
        return
    try:
        status = {
            'state': state,
            'lastRun': datetime.now(timezone.utc).isoformat(),
            'summary': summary[:280],
            'ok': ok,
        }
        if metrics:
            status['metrics'] = metrics[:3]
        payload = json.dumps({'agentId': 'growth', 'status': status}).encode()
        req = urllib.request.Request(
            f"{_CEOS_URL.rstrip('/')}/api/report",
            data=payload,
            headers={'x-report-secret': secret, 'content-type': 'application/json'},
            method='POST',
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f'[ceo_report] {e}')


def _age_days(dt_str: str) -> float:
    """Days since a UTC ISO timestamp."""
    if not dt_str:
        return 0
    try:
        dt = datetime.fromisoformat(str(dt_str).replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 86400
    except Exception:
        return 0


def find_due_followups(db: Database) -> list[tuple[dict, str]]:
    """Return (business, next_version) pairs that are ready for follow-up."""
    rows = db.get_all()
    due = []
    for b in rows:
        status = b.get('outreach_status') or 'new'
        if status in ('new', 'unsubscribed', 'closed'):
            continue
        if b.get('outreach_replied_at'):
            continue  # already replied, don't pester
        if not b.get('demo_url') or not b.get('owner_email'):
            continue

        sent_at = str(b.get('outreach_sent_at') or '')
        body_id = b.get('outreach_body_id') or 'v1'
        age = _age_days(sent_at)

        if body_id == 'v1' and age >= V2_DELAY_DAYS:
            due.append((b, 'v2'))
        elif body_id == 'v2' and age >= V3_DELAY_DAYS:
            due.append((b, 'v3'))

    return due[:MAX_PER_RUN]


def run(dry_run: bool = False):
    db = Database()
    due = find_due_followups(db)

    if not due:
        print('No follow-ups due today.')
        return 0

    print(f'{"[DRY RUN] " if dry_run else ""}Sending {len(due)} follow-ups...\n')

    sent = 0
    for biz, version in due:
        print(f'  {version} → {biz["name"]} ({biz["owner_email"]})')
        if not dry_run:
            try:
                outreach_email.send(biz['place_id'], version=version)
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
        _report('ok', summary, metrics=[
            {'label': 'Leads', 'value': total},
            {'label': 'Sites built', 'value': sites},
            {'label': 'Emails', 'value': emailed},
        ])

    print(f'\nDone. {sent} follow-ups {"(dry run)" if dry_run else "sent"}.')
    return sent


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    run(dry_run=args.dry_run)

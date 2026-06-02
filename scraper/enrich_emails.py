"""
Email enrichment for scraped businesses.

Strategy (in order):
  1. If business has a stored website URL → fetch that page + /contact for email
  2. DuckDuckGo HTML search → extract emails from result snippets
  3. (Optional) Google Custom Search if GOOGLE_CSE_ID is set

Writes owner_email to the database for any match found.
Rate-limited to ~1 req/sec — safe to run against 133 businesses.

Usage:
    cd scraper
    python enrich_emails.py                  # enrich all missing
    python enrich_emails.py --limit 20       # cap per run
    python enrich_emails.py --re-enrich      # retry already-enriched rows
"""
from __future__ import annotations
import os
import re
import sys
import time
import json
import argparse
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
sys.path.insert(0, os.path.dirname(__file__))
from db import Database

_CEOS_URL = os.environ.get('CEOS_DASHBOARD_URL', 'https://ceos-enterprise.vercel.app')

# Email regex — intentionally broad, then filtered
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

# Domains that are never real business owner emails
_JUNK_DOMAINS = {
    'sentry.io', 'example.com', 'wixpress.com', 'squarespace.com',
    'facebook.com', 'instagram.com', 'twitter.com', 'google.com',
    'apple.com', 'microsoft.com', 'amazonaws.com', 'cloudflare.com',
    'mailchimp.com', 'sendgrid.net', 'resend.com',
}
_JUNK_PREFIXES = {'noreply', 'no-reply', 'donotreply', 'mailer', 'bounce',
                  'admin', 'postmaster', 'abuse', 'webmaster', 'privacy',
                  'support@google', 'support@apple'}

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


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


def _fetch(url: str, timeout: int = 10) -> str:
    """Fetch URL, return decoded HTML or empty string on failure."""
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = 'utf-8'
            ct = resp.headers.get('Content-Type', '')
            if 'charset=' in ct:
                charset = ct.split('charset=')[-1].strip().split(';')[0]
            return resp.read().decode(charset, errors='replace')
    except Exception as e:
        print(f'    fetch error ({url[:60]}): {type(e).__name__}')
        return ''


def _clean_emails(raw: list[str]) -> list[str]:
    """Dedupe and filter junk emails, return best candidates first."""
    seen = set()
    out = []
    for email in raw:
        email = email.lower().strip('.')
        if email in seen:
            continue
        seen.add(email)
        domain = email.split('@', 1)[-1]
        prefix = email.split('@', 1)[0]
        if domain in _JUNK_DOMAINS:
            continue
        if any(email.startswith(j) for j in _JUNK_PREFIXES):
            continue
        if '.png' in email or '.jpg' in email or '.gif' in email:
            continue
        out.append(email)
    # Prefer gmail/yahoo/outlook (personal) → likely the owner
    personal = [e for e in out if any(d in e for d in ('gmail', 'yahoo', 'hotmail', 'outlook', 'icloud'))]
    business = [e for e in out if e not in personal]
    return personal + business


def _extract_emails(html: str) -> list[str]:
    raw = _EMAIL_RE.findall(html)
    # Also unescape HTML entities like &amp; → &
    html2 = html.replace('&amp;', '&').replace('&#64;', '@').replace('%40', '@')
    raw += _EMAIL_RE.findall(html2)
    return _clean_emails(raw)


def _from_website(url: str) -> str | None:
    """Try to find an email on a business's stored website."""
    # Skip booking platforms / social — no email there
    skip_hosts = {'booksy.com', 'square.site', 'squareup.com', 'edan.io',
                  'mindbodyonline.com', 'styleseat.com', 'schedulicity.com',
                  'fresha.com', 'vagaro.com'}
    try:
        host = urllib.parse.urlparse(url).netloc.replace('www.', '')
    except Exception:
        return None
    if any(s in host for s in skip_hosts):
        return None

    html = _fetch(url)
    emails = _extract_emails(html)
    if emails:
        return emails[0]

    # Try /contact subpage
    base = url.rstrip('/')
    for path in ('/contact', '/contact-us', '/contact.html'):
        time.sleep(0.8)
        html = _fetch(base + path)
        emails = _extract_emails(html)
        if emails:
            return emails[0]

    return None


def _from_facebook(url: str) -> str | None:
    """Try Facebook mobile about page."""
    # Convert to mobile URL
    mobile = url.replace('www.facebook.com', 'm.facebook.com')
    if 'profile.php' in mobile:
        # Can't easily get about page for numeric IDs
        page_html = _fetch(mobile)
    else:
        about_url = mobile.rstrip('/') + '/about'
        page_html = _fetch(about_url)
    emails = _extract_emails(page_html)
    return emails[0] if emails else None


def _from_ddg(name: str, address: str) -> str | None:
    """DuckDuckGo HTML search — no API key needed."""
    city = 'Berkeley'
    # Try to extract a more specific area from address
    if address:
        parts = address.split(',')
        if len(parts) > 1:
            city = parts[1].strip()

    query = f'"{name}" {city} email contact'
    url = 'https://html.duckduckgo.com/html/?' + urllib.parse.urlencode({'q': query})
    html = _fetch(url, timeout=15)
    emails = _extract_emails(html)
    if emails:
        return emails[0]

    # Second try: broader
    query2 = f'{name} Berkeley CA email'
    url2 = 'https://html.duckduckgo.com/html/?' + urllib.parse.urlencode({'q': query2})
    time.sleep(2)
    html2 = _fetch(url2, timeout=15)
    emails2 = _extract_emails(html2)
    return emails2[0] if emails2 else None


def enrich_one(biz: dict) -> str | None:
    """Try all strategies, return first email found or None."""
    website = (biz.get('website') or '').strip()

    # Strategy 1: stored website
    if website and 'facebook.com' in website:
        print(f'    → Facebook page...')
        email = _from_facebook(website)
        if email:
            return email
        time.sleep(1)

    if website and 'facebook.com' not in website and 'instagram.com' not in website:
        print(f'    → website ({website[:40]})...')
        email = _from_website(website)
        if email:
            return email
        time.sleep(1)

    # Strategy 2: DuckDuckGo
    print(f'    → DuckDuckGo search...')
    email = _from_ddg(biz['name'], biz.get('address', ''))
    time.sleep(2.5)
    return email


def run(limit: int | None = None, re_enrich: bool = False):
    db = Database()
    rows = db.get_all()

    pending = [
        b for b in rows
        if (not b.get('owner_email') or re_enrich)
    ]
    if limit:
        pending = pending[:limit]

    total = len(pending)
    print(f'Enriching emails for {total} businesses...\n')

    found = 0
    for i, biz in enumerate(pending):
        print(f'[{i+1}/{total}] {biz["name"]}')
        try:
            email = enrich_one(biz)
        except Exception as e:
            print(f'    error: {e}')
            email = None

        if email:
            db.update_business(biz['place_id'], owner_email=email)
            found += 1
            print(f'    ✓ {email}')
        else:
            print(f'    — not found')

    # Summary
    all_rows = db.get_all()
    total_db = len(all_rows)
    with_email = sum(1 for b in all_rows if b.get('owner_email'))
    sites_built = sum(1 for b in all_rows if b.get('demo_url'))
    emailed = sum(1 for b in all_rows if b.get('outreach_status') not in (None, 'new'))
    summary = (
        f'{total_db} scraped · {sites_built} sites built · '
        f'{with_email} emails found · {emailed} outreach sent'
    )
    print(f'\nDone. Found {found} new emails this run.')
    print(f'Dashboard: {summary}')
    _report('ok', summary)
    return found


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--re-enrich', action='store_true')
    args = parser.parse_args()
    run(limit=args.limit, re_enrich=args.re_enrich)

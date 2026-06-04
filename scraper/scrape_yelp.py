"""
Yelp email & phone enrichment.

Strategy:
  1. For businesses that already have a yelp.com URL stored → scrape that page.
  2. For all others → search Yelp for "{name} {city}" and scrape the top result.
  3. From each Yelp page, extract:
       - Email address (in "From the Business" section, schema.org, or visible text)
       - Phone (fallback if Google didn't return one)
       - Website URL (sometimes the real owner site is listed here)
  4. Write any findings to owner_email / phone in the DB.

Rate-limited to ~1 request per 4 seconds to avoid 503s from Yelp.

Usage:
    cd scraper
    python scrape_yelp.py                # enrich all businesses missing email
    python scrape_yelp.py --limit 30     # cap per run
    python scrape_yelp.py --re-enrich    # retry already-enriched rows
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

_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

_JUNK_DOMAINS = {
    'yelp.com', 'yelpcdn.com', 'biz.yelp.com', 'sentry.io', 'sentry-next.wixpress.com',
    'wixpress.com', 'example.com', 'squarespace.com', 'facebook.com', 'instagram.com',
    'twitter.com', 'google.com', 'apple.com', 'microsoft.com', 'amazonaws.com',
    'cloudflare.com', 'duckduckgo.com', 'schema.org', 'w3.org', 'fonts.gstatic.com',
}
_JUNK_PREFIXES = {
    'noreply', 'no-reply', 'donotreply', 'mailer', 'bounce', 'admin',
    'postmaster', 'abuse', 'webmaster', 'privacy', 'error-lite', 'error',
    'support@yelp', 'press@', 'legal@', 'security@',
}

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
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


def _fetch(url: str, timeout: int = 12) -> str:
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            # Handle gzip
            if resp.info().get('Content-Encoding') == 'gzip':
                import gzip
                raw = gzip.decompress(raw)
            return raw.decode('utf-8', errors='replace')
    except Exception as e:
        print(f'    fetch error ({url[:60]}): {type(e).__name__}')
        return ''


def _clean_email(email: str) -> str | None:
    email = email.lower().strip('.')
    domain = email.split('@', 1)[-1]
    if domain in _JUNK_DOMAINS:
        return None
    if any(email.startswith(p) for p in _JUNK_PREFIXES):
        return None
    if any(x in email for x in ('.png', '.jpg', '.gif', '.js', '.css')):
        return None
    return email


def _extract_emails(html: str) -> list[str]:
    # Also catch obfuscated @ signs
    html2 = (html
        .replace('&#64;', '@').replace('%40', '@')
        .replace('[at]', '@').replace(' at ', '@')
        .replace('&amp;', '&'))
    raw = _EMAIL_RE.findall(html) + _EMAIL_RE.findall(html2)
    seen: set[str] = set()
    out: list[str] = []
    for e in raw:
        c = _clean_email(e)
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    # Prefer personal emails (gmail/yahoo) over generic business ones
    personal = [e for e in out if any(d in e for d in ('gmail', 'yahoo', 'hotmail', 'outlook', 'icloud'))]
    business = [e for e in out if e not in personal]
    return personal + business


def _yelp_search_url(name: str, city: str) -> str:
    q = urllib.parse.urlencode({'find_desc': name, 'find_loc': city})
    return f'https://www.yelp.com/search?{q}'


def _extract_yelp_biz_url(search_html: str) -> str | None:
    """Extract first business URL from Yelp search results page."""
    # Yelp search results embed JSON with business links
    patterns = [
        r'"businessUrl":\s*"(/biz/[^"]+)"',
        r'href="(/biz/[a-z0-9\-]+)"',
        r'"url":\s*"(https://www\.yelp\.com/biz/[^"]+)"',
    ]
    for pat in patterns:
        m = re.search(pat, search_html)
        if m:
            url = m.group(1)
            if not url.startswith('http'):
                url = 'https://www.yelp.com' + url
            # Strip query params
            return url.split('?')[0]
    return None


def _scrape_yelp_page(biz_url: str) -> dict:
    """Scrape a Yelp business page for email, phone, and website."""
    html = _fetch(biz_url)
    if not html:
        return {}

    result: dict = {}

    # Email
    emails = _extract_emails(html)
    if emails:
        result['email'] = emails[0]

    # Phone — Yelp embeds it in multiple formats
    phone_patterns = [
        r'"telephone":\s*"([^"]+)"',
        r'href="tel:([^"]+)"',
        r'<p[^>]*class="[^"]*phone[^"]*"[^>]*>([^<]+)<',
    ]
    for pat in phone_patterns:
        m = re.search(pat, html, re.I)
        if m:
            phone = re.sub(r'[^\d+\-() ]', '', m.group(1)).strip()
            if len(phone) >= 10:
                result['phone'] = phone
                break

    # Website listed on Yelp (could be a real owned site we missed)
    website_patterns = [
        r'"website":\s*"([^"]+)"',
        r'href="([^"]+)"[^>]*rel="noopener[^"]*nofollow',
        r'businessUrl.*?href="(https?://(?!www\.yelp)[^"]+)"',
    ]
    for pat in website_patterns:
        m = re.search(pat, html, re.I)
        if m:
            site = m.group(1)
            if site.startswith('http') and 'yelp.com' not in site:
                result['website'] = site
                break

    return result


def enrich_one(biz: dict) -> dict:
    """Try Yelp for one business. Returns dict of found fields."""
    website = (biz.get('website') or '').strip()
    name = biz['name']
    address = biz.get('address', '')
    city = address.split(',')[1].strip() if ',' in address else 'Berkeley CA'

    yelp_url: str | None = None

    # Direct URL if already have a Yelp link
    if 'yelp.com/biz' in website:
        yelp_url = website.split('?')[0]
        print(f'    → direct Yelp: {yelp_url}')
    else:
        # Search Yelp
        search_url = _yelp_search_url(name, city)
        print(f'    → Yelp search: {name} in {city}')
        search_html = _fetch(search_url)
        time.sleep(4)
        if search_html:
            yelp_url = _extract_yelp_biz_url(search_html)
            if yelp_url:
                print(f'    → found: {yelp_url}')

    if not yelp_url:
        return {}

    time.sleep(3)
    data = _scrape_yelp_page(yelp_url)

    # Also try /biz/name?source=biz_details_web_external_bizyou link on Yelp which
    # sometimes exposes email in a contact section — fetch a second time
    if not data.get('email') and yelp_url:
        time.sleep(3)
        data2 = _scrape_yelp_page(yelp_url + '#contact')
        if data2.get('email'):
            data['email'] = data2['email']

    return data


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
    print(f'Yelp enrichment for {total} businesses...\n')

    found_emails = 0
    found_phones = 0

    for i, biz in enumerate(pending):
        print(f'[{i+1}/{total}] {biz["name"]}')
        try:
            data = enrich_one(biz)
        except Exception as e:
            print(f'    error: {e}')
            data = {}

        updates: dict = {}
        if data.get('email'):
            updates['owner_email'] = data['email']
            found_emails += 1
            print(f'    ✓ email: {data["email"]}')
        if data.get('phone') and not biz.get('phone'):
            updates['phone'] = data['phone']
            found_phones += 1
            print(f'    ✓ phone: {data["phone"]}')
        if not data.get('email') and not data.get('phone'):
            print(f'    — nothing found')

        if updates:
            db.update_business(biz['place_id'], **updates)

        time.sleep(4)

    all_rows = db.get_all()
    total_db = len(all_rows)
    with_email = sum(1 for b in all_rows if b.get('owner_email'))
    sites = sum(1 for b in all_rows if b.get('demo_url'))
    emailed = sum(1 for b in all_rows if b.get('outreach_status') not in (None, 'new'))
    summary = (
        f'{total_db} scraped · {sites} sites · '
        f'{with_email} emails · {emailed} outreach sent'
    )
    print(f'\nDone. Found {found_emails} emails, {found_phones} phones.')
    print(f'Dashboard: {summary}')
    _report('ok', summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--re-enrich', action='store_true')
    args = parser.parse_args()
    run(limit=args.limit, re_enrich=args.re_enrich)

"""
Send cold outreach emails via Resend.

Two-tier pricing:
  Basic    $299  — transfer the auto-generated demo site as-is
  Premium  $599  — full custom redesign: unique layout, 5 pages,
                   professional copy, domain setup, SEO basics

Usage:
    cd outreach
    python email.py --place-id <place_id> --dry-run          # preview
    python email.py --place-id <place_id>                     # send v1
    python email.py --place-id <place_id> --version v2        # follow-up
    python email.py --list                                     # pipeline status
"""
import os
import sys
import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'scraper', '.env'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scraper'))
from db import Database

import resend

resend.api_key = os.environ.get('RESEND_API_KEY', '')

FROM_NAME = 'Charles'
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'charles@yourdomain.com')
PHYSICAL_ADDRESS = 'Berkeley, CA 94704'

# Portfolio page hosted on ceos-enterprise (or standalone domain later)
PORTFOLIO_URL = os.environ.get('PORTFOLIO_URL', 'https://ceos-enterprise.vercel.app/portfolio')


def _first_name(owner: str) -> str:
    if not owner or owner.lower() in ('team', 'owner'):
        return 'there'
    return owner.split()[0]


def build_email(version: str, name: str, owner: str, demo_url: str) -> tuple[str, str]:
    first = _first_name(owner)

    if version == 'v1':
        subject = f"Built a website for {name} — take a look?"
        body = f"""Hi {first},

I'm a UC Berkeley student who builds websites for local businesses. I put one together for {name} this week using your real photos and info:

👉 {demo_url}

Two options if you want to keep it:

  · Basic ($299) — I transfer the site to you as-is. You own it.
  · Custom ($599) — I redesign it from scratch with a unique layout,
    5 pages, professional copy, and domain setup.

Here are examples of other sites I've built:
{PORTFOLIO_URL}

No pressure either way — if it's not for you, I'll take it down.

— Charles
UC Berkeley · charles_ow@berkeley.edu"""

    elif version == 'v2':
        subject = f"Re: Website for {name}"
        body = f"""Hi {first},

Bumping this in case it got buried. The {name} demo is still live:

👉 {demo_url}

Quick reminder on pricing:
  · Basic transfer: $299
  · Full custom redesign: $599 (portfolio: {PORTFOLIO_URL})

Happy to jump on a quick call or answer any questions — just reply here.

— Charles"""

    elif version == 'v3':
        subject = f"Last note — {name} site"
        body = f"""Hi {first},

Last note before I take the {name} demo down to free up the URL.

Demo: {demo_url}
Portfolio: {PORTFOLIO_URL}

Basic transfer $299 · Custom redesign $599

If you want it, just reply "yes" and I'll handle the rest. If not, no worries — wishing {name} the best.

— Charles"""

    else:
        raise ValueError(f"Unknown version: {version}")

    return subject, body


def to_html(body: str, demo_url: str, name: str) -> str:
    """Rich HTML version with a demo preview button."""
    paragraphs = body.strip().split('\n\n')
    html_paras = []
    for p in paragraphs:
        # Make emoji lines stand out
        lines = p.replace(chr(10), '<br>')
        html_paras.append(f'<p style="margin:0 0 16px 0">{lines}</p>')

    cta_button = f"""
<table cellpadding="0" cellspacing="0" style="margin:20px 0">
  <tr>
    <td>
      <a href="{demo_url}"
         style="display:inline-block;background:#111;color:#fff;font-size:14px;
                font-weight:600;text-decoration:none;padding:12px 24px;
                border-radius:8px;border:1px solid #333">
        View {name} demo →
      </a>
    </td>
    <td style="padding-left:12px">
      <a href="{PORTFOLIO_URL}"
         style="display:inline-block;color:#555;font-size:13px;text-decoration:none;
                padding:12px 16px;border:1px solid #e5e5e5;border-radius:8px">
        See portfolio
      </a>
    </td>
  </tr>
</table>"""

    pricing_box = """
<table cellpadding="0" cellspacing="0" style="margin:20px 0;width:100%;border-collapse:collapse">
  <tr>
    <td style="padding:14px 16px;border:1px solid #e5e5e5;border-radius:8px 0 0 8px;
               background:#fafafa;width:50%;vertical-align:top">
      <div style="font-size:12px;color:#999;text-transform:uppercase;letter-spacing:.5px">Basic</div>
      <div style="font-size:22px;font-weight:700;margin:4px 0">$299</div>
      <div style="font-size:13px;color:#555;line-height:1.5">
        Demo site transferred to you<br>
        Mobile-responsive<br>
        Your real photos &amp; info<br>
        You own it outright
      </div>
    </td>
    <td style="width:8px"></td>
    <td style="padding:14px 16px;border:2px solid #111;border-radius:0 8px 8px 0;
               background:#fff;width:50%;vertical-align:top">
      <div style="font-size:12px;color:#999;text-transform:uppercase;letter-spacing:.5px">Custom ✦</div>
      <div style="font-size:22px;font-weight:700;margin:4px 0">$599</div>
      <div style="font-size:13px;color:#555;line-height:1.5">
        Unique custom design<br>
        5 pages + professional copy<br>
        Domain setup &amp; SEO basics<br>
        2 rounds of revisions
      </div>
    </td>
  </tr>
</table>"""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;
             font-size:15px;line-height:1.6;color:#111;max-width:580px;margin:0 auto;padding:32px 24px">
  {''.join(html_paras[:2])}
  {cta_button}
  {pricing_box}
  {''.join(html_paras[2:])}
  <hr style="border:none;border-top:1px solid #e5e5e5;margin:28px 0">
  <p style="font-size:12px;color:#999;margin:0">
    {FROM_NAME} · UC Berkeley · {PHYSICAL_ADDRESS}<br>
    To unsubscribe, reply "unsubscribe."
  </p>
</body>
</html>"""


def send(place_id: str, version: str = 'v1', dry_run: bool = False):
    db = Database()
    biz = db.get_business(place_id)
    if not biz:
        sys.exit(f'Business not found: {place_id}')
    if not biz.get('demo_url'):
        sys.exit(f'No demo URL for {biz["name"]} — run generator/generate.py first.')

    owner = biz.get('owner_name') or 'owner'
    subject, body = build_email(version, biz['name'], owner, biz['demo_url'])

    print(f'To:      {biz.get("owner_email") or "(no email set)"}')
    print(f'Subject: {subject}')
    print(f'\n{body}\n')

    if dry_run:
        print('[DRY RUN — not sent]')
        return

    to_email = biz.get('owner_email')
    if not to_email:
        sys.exit(f'No email address for {biz["name"]} — enrich first.')

    html = to_html(body, biz['demo_url'], biz['name'])
    result = resend.Emails.send({
        'from': f'{FROM_NAME} <{FROM_EMAIL}>',
        'to': [to_email],
        'subject': subject,
        'html': html,
        'text': body,
    })

    db.update_business(
        place_id,
        outreach_sent_at=datetime.now(timezone.utc).isoformat(),
        outreach_channel='email',
        outreach_subject=subject,
        outreach_body_id=version,
        outreach_status='sent',
    )
    print(f'Sent {version} to {to_email}  (id: {result.get("id")})')


def list_pipeline():
    db = Database()
    rows = db.get_all()
    print(f'\n{"Name":<35} {"Status":<12} {"Outreach":<10} {"Email"}')
    print('-' * 100)
    for b in rows:
        if b.get('demo_url') or b.get('owner_email'):
            print(f'{b["name"]:<35} {(b["status"] or ""):<12} '
                  f'{(b["outreach_status"] or "new"):<10} {b.get("owner_email") or ""}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--place-id')
    parser.add_argument('--version', default='v1', choices=['v1', 'v2', 'v3'])
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()

    if args.list:
        list_pipeline()
    elif args.place_id:
        send(args.place_id, args.version, args.dry_run)
    else:
        parser.print_help()

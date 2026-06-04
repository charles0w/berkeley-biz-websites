"""
Send cold outreach emails via Resend.

Pitch: preview-first → 10-min call → buy as-is or custom build.

Usage:
    cd outreach
    python email.py --place-id <place_id> --dry-run
    python email.py --place-id <place_id>
    python email.py --place-id <place_id> --version v2
    python email.py --list
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
PORTFOLIO_URL = os.environ.get('PORTFOLIO_URL', 'https://ceos-enterprise.vercel.app/portfolio')
PHONE_NUMBER = os.environ.get('OUTREACH_PHONE', '')  # optional: add your number as GH secret


def _first_name(owner: str) -> str:
    if not owner or owner.lower() in ('team', 'owner'):
        return 'there'
    return owner.split()[0]


def build_email(version: str, name: str, owner: str, demo_url: str,
                rating: float = 0, review_count: int = 0) -> tuple[str, str]:
    first = _first_name(owner)
    stars = f'{rating}★ ({review_count} reviews)' if rating else ''

    if version == 'v1':
        subject = f"Free website preview I made for {name}"
        body = f"""Hi {first},

I'm Charles — a UC Berkeley student who builds websites for local Berkeley businesses. I put together a free preview site for {name} this week, built from your real Google Maps photos and info:

👉 {demo_url}

This is just a preview — I haven't sent you a bill, and I'm not asking you to commit to anything.

I'd love to hop on a quick 10-minute call to show you what a fully custom version could look like, or answer any questions. No pressure at all.

Three options — pick what fits:

  · Basic ($299 one-time) — transfer the preview site as-is. You own it.
  · Custom ($599 one-time) — unique design, 5 pages, professional copy, domain setup.
  · Pro ($49/mo) — everything in Custom plus: AI chat widget that answers
    customer questions 24/7, online booking so customers schedule appointments
    directly from your site, automated SMS/email reminders that cut no-shows,
    and monthly updates handled by me.

Examples of what I've built for other Berkeley businesses:
{PORTFOLIO_URL}

The Pro plan is especially useful for salons, barbershops, cafes — any business where
bookings and repeat customers drive revenue. Most clients who try it see it pay for
itself within the first month from reduced no-shows alone.

If a call works, just reply with a time and I'll make it happen. Even a quick "not interested" helps — I'll move on and won't bother you again.

— Charles
UC Berkeley · {FROM_EMAIL}"""

    elif version == 'v2':
        subject = f"Re: Free website preview for {name}"
        body = f"""Hi {first},

Following up on the free preview site I built for {name}:

👉 {demo_url}

I know inboxes get busy. Quick version: I'd love a 10-minute call to walk you through what a fully custom site for {name} could look like — or if you want the preview as-is, it's $299 and I handle the transfer.

A few things worth knowing:
  · {name} has {stars + ' on Google — ' if stars else ''}no website means you're invisible to anyone who searches for you online
  · Most of your competitors in Berkeley already have sites; this closes that gap fast
  · The call is free, no-commitment, and I can work around your schedule

If this isn't the right time, just say so — I respect that completely.

— Charles
{FROM_EMAIL}"""

    elif version == 'v3':
        subject = f"Last note — {name} preview site"
        body = f"""Hi {first},

Last note from me — I'm going to repurpose the {name} URL for another business by end of week if I don't hear back.

Preview: {demo_url}

If you'd like to keep it:
  · Basic: $299 one-time (transfer as-is, you own it)
  · Custom: $599 one-time (unique design, 5 pages, domain setup)
  · Pro: $49/mo (Custom + AI chat, online booking, SMS reminders)
  · Or just reply to schedule a free 10-min call — no commitment

If the timing isn't right, no worries. I wish {name} the best.

— Charles
{FROM_EMAIL}"""

    else:
        raise ValueError(f"Unknown version: {version}")

    return subject, body


def to_html(body: str, demo_url: str, name: str) -> str:
    paragraphs = body.strip().split('\n\n')
    html_parts = []
    for p in paragraphs:
        lines = p.strip().split('\n')
        # Detect bullet lists (lines starting with ·)
        if any(l.strip().startswith('·') for l in lines):
            items = ''.join(
                f'<li style="margin:0 0 8px 0;padding-left:4px">{l.strip().lstrip("· ")}</li>'
                for l in lines if l.strip()
            )
            html_parts.append(f'<ul style="margin:0 0 16px 0;padding-left:20px;list-style:disc">{items}</ul>')
        else:
            text = p.replace('\n', '<br>')
            html_parts.append(f'<p style="margin:0 0 16px 0">{text}</p>')

    preview_button = f"""
<table cellpadding="0" cellspacing="0" style="margin:24px 0">
  <tr>
    <td>
      <a href="{demo_url}"
         style="display:inline-block;background:#111;color:#fff;font-size:14px;
                font-weight:600;text-decoration:none;padding:14px 28px;
                border-radius:6px;border:1px solid #333;letter-spacing:0.01em">
        View {name} preview →
      </a>
    </td>
  </tr>
</table>"""

    call_box = f"""
<table cellpadding="0" cellspacing="0" style="margin:24px 0;width:100%;max-width:480px;
       border:1px solid #e8e8e8;border-radius:8px">
  <tr>
    <td style="padding:20px 24px">
      <p style="margin:0 0 4px;font-size:13px;color:#999;text-transform:uppercase;
                letter-spacing:0.05em;font-weight:600">How this works</p>
      <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#111">
        Free 10-minute call
      </p>
      <p style="margin:0;font-size:13px;color:#555;line-height:1.5">
        Reply with a time that works and I'll walk you through
        what a custom site for {name} could look like.
        No commitment, no sales pitch — just a quick look.
      </p>
    </td>
  </tr>
</table>"""

    pricing_table = f"""
<table cellpadding="0" cellspacing="0" style="margin:20px 0;width:100%;max-width:480px;border-collapse:collapse">
  <tr>
    <td style="padding:14px 16px;border:1px solid #e8e8e8;border-radius:8px 0 0 8px;
               background:#fafafa;width:50%;vertical-align:top">
      <div style="font-size:11px;color:#999;text-transform:uppercase;letter-spacing:0.05em">As-is transfer</div>
      <div style="font-size:24px;font-weight:700;margin:4px 0;color:#111">$299</div>
      <div style="font-size:12px;color:#555;line-height:1.5">
        Preview site transferred to you<br>You own it outright<br>No subscriptions
      </div>
    </td>
    <td style="width:8px"></td>
    <td style="padding:14px 16px;border:2px solid #111;border-radius:0 8px 8px 0;
               background:#fff;width:50%;vertical-align:top">
      <div style="font-size:11px;color:#999;text-transform:uppercase;letter-spacing:0.05em">Custom build ✦</div>
      <div style="font-size:24px;font-weight:700;margin:4px 0;color:#111">$599</div>
      <div style="font-size:12px;color:#555;line-height:1.5">
        Unique design for your brand<br>5 pages + pro copy<br>Domain &amp; SEO setup
      </div>
    </td>
  </tr>
</table>"""

    body_html = ''.join(html_parts)

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;
             font-size:15px;line-height:1.6;color:#111;max-width:580px;margin:0 auto;padding:32px 24px">

  {body_html[:body_html.find('<p style="margin:0 0 16px 0">👉')]}

  {preview_button}

  {body_html[body_html.find('<p style="margin:0 0 16px 0">This is just'):]}

  {call_box}
  {pricing_table}

  <hr style="border:none;border-top:1px solid #eee;margin:28px 0">
  <p style="font-size:12px;color:#aaa;margin:0">
    {FROM_NAME} · UC Berkeley · {PHYSICAL_ADDRESS}<br>
    To unsubscribe, reply "unsubscribe."
  </p>
</body>
</html>"""


def _simple_html(body: str, demo_url: str, name: str) -> str:
    """Simple HTML for v2/v3 — no complex layout needed."""
    paragraphs = body.strip().split('\n\n')
    html_parts = []
    for p in paragraphs:
        lines = p.strip().split('\n')
        if any(l.strip().startswith('·') for l in lines):
            items = ''.join(
                f'<li style="margin:0 0 8px">{l.strip().lstrip("· ")}</li>'
                for l in lines if l.strip()
            )
            html_parts.append(f'<ul style="margin:0 0 16px;padding-left:20px">{items}</ul>')
        else:
            html_parts.append(f'<p style="margin:0 0 16px">{p.replace(chr(10),"<br>")}</p>')

    # Inject a prominent button after first paragraph
    button = f'<table cellpadding="0" cellspacing="0" style="margin:20px 0"><tr><td><a href="{demo_url}" style="display:inline-block;background:#111;color:#fff;font-size:14px;font-weight:600;text-decoration:none;padding:12px 24px;border-radius:6px">View {name} preview →</a></td></tr></table>'
    html_parts.insert(1, button)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;
             font-size:15px;line-height:1.6;color:#111;max-width:580px;margin:0 auto;padding:32px 24px">
  {''.join(html_parts)}
  <hr style="border:none;border-top:1px solid #eee;margin:28px 0">
  <p style="font-size:12px;color:#aaa;margin:0">
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
        sys.exit(f'No demo URL for {biz["name"]} — generate site first.')

    owner = biz.get('owner_name') or 'owner'
    rating = float(biz.get('rating') or 0)
    review_count = int(biz.get('review_count') or 0)
    subject, body = build_email(version, biz['name'], owner, biz['demo_url'],
                                rating=rating, review_count=review_count)

    print(f'To:      {biz.get("owner_email") or "(no email set)"}')
    print(f'Subject: {subject}')
    print(f'\n{body}\n')

    if dry_run:
        print('[DRY RUN — not sent]')
        return

    to_email = biz.get('owner_email')
    if not to_email:
        sys.exit(f'No email for {biz["name"]} — enrich first.')

    html = _simple_html(body, biz['demo_url'], biz['name']) if version != 'v1' else _simple_html(body, biz['demo_url'], biz['name'])

    result = resend.Emails.send({
        'from': f'{FROM_NAME} <{FROM_EMAIL}>',
        'to': [to_email],
        'subject': subject,
        'html': html,
        'text': body,
        'reply_to': FROM_EMAIL,
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

"""
Send cold outreach emails via Resend.

Usage:
    cd outreach
    python email.py --place-id <place_id> --dry-run          # preview
    python email.py --place-id <place_id>                     # send v1
    python email.py --place-id <place_id> --version v2        # follow-up
    python email.py --list                                     # show outreach pipeline status
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

FROM_NAME = 'Charles Ouch'
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'charles@yourdomain.com')
PHYSICAL_ADDRESS = 'Berkeley, CA 94704'


def build_email(version: str, name: str, owner: str, demo_url: str) -> tuple[str, str]:
    first = owner.split()[0] if owner and owner.lower() != 'team' else 'team'

    if version == 'v1':
        subject = f"I made a website for {name} — feedback?"
        body = f"""Hi {first},

I'm a UC Berkeley student building polished websites for local Berkeley businesses. I made one for {name} over the weekend — using your real photos and info from Google Maps:

{demo_url}

If you like it, I'll transfer it to you for a one-time $299. If you don't, no worries — costs you nothing to look.

— Charles"""

    elif version == 'v2':
        subject = f"Re: I made a website for {name} — feedback?"
        body = f"""Quick bump in case my last email got buried — I built a sample site for {name} here:

{demo_url}

Happy to send it over for $299 (or $249 this week if you grab it before Friday). If it's not for you, I'll take it down — just let me know.

— Charles"""

    elif version == 'v3':
        subject = f"Last note about the {name} site"
        body = f"""Hi {first},

Last note — I'll keep the {name} demo up for one more week and then take it down to free up the URL for another business. If you'd like it, just reply "yes" and I'll send the transfer.

If not, no worries — wishing {name} the best.

— Charles"""

    else:
        raise ValueError(f"Unknown version: {version}")

    return subject, body


def to_html(body: str) -> str:
    paragraphs = body.strip().split('\n\n')
    html_paras = ''.join(f'<p style="margin:0 0 16px 0">{p.replace(chr(10), "<br>")}</p>' for p in paragraphs)
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;font-size:15px;line-height:1.6;color:#111111;max-width:560px;margin:0 auto;padding:32px 24px">
  {html_paras}
  <hr style="border:none;border-top:1px solid #e5e5e5;margin:28px 0">
  <p style="font-size:12px;color:#999;margin:0">
    {FROM_NAME} · UC Berkeley · {PHYSICAL_ADDRESS}<br>
    To unsubscribe, reply with "unsubscribe."
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

    owner = biz.get('owner_name') or 'team'
    subject, body = build_email(version, biz['name'], owner, biz['demo_url'])

    print(f'To:      {biz.get("owner_email") or "(no email set)"}')
    print(f'Subject: {subject}')
    print(f'\n{body}\n')

    if dry_run:
        print('[DRY RUN — not sent]')
        return

    to_email = biz.get('owner_email')
    if not to_email:
        sys.exit(f'No email address for {biz["name"]} — set owner_email in the DB first.')

    result = resend.Emails.send({
        'from': f'{FROM_NAME} <{FROM_EMAIL}>',
        'to': [to_email],
        'subject': subject,
        'html': to_html(body),
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
    print(f'\n{"Name":<35} {"Status":<12} {"Outreach":<12} {"Email"}')
    print('-' * 95)
    for b in rows:
        if b.get('demo_url') or b.get('owner_email'):
            print(f'{b["name"]:<35} {(b["status"] or ""):<12} {(b["outreach_status"] or "new"):<12} {b.get("owner_email") or ""}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--place-id', help='Google place_id to email')
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

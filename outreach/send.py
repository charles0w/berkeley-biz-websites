"""
Send cold outreach emails and follow-ups to businesses.

Sending backend (priority order):
  1. Gmail SMTP  — set SMTP_PASS in .env (Google App Password for charles_ow@berkeley.edu)
                   Go to myaccount.google.com → Security → App passwords → generate one
  2. Resend API  — set RESEND_API_KEY and FROM_ADDRESS in .env (needs verified domain)

Usage:
    python send.py --list                          # businesses ready for outreach (site built + email set)
    python send.py --preview <place_id>            # print email without sending
    python send.py --send <place_id>               # send cold email to one business
    python send.py --send-all                      # send cold email to all ready businesses (caps at 20/day)
    python send.py --follow-ups                    # send due follow-ups (day 4 and day 10)
    python send.py --set-email <place_id> <email>  # add owner email to database
    python send.py --set-name <place_id> <name>    # add owner first name to database
"""

import argparse
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scraper"))
from db import get_business, get_businesses_ready_for_outreach, mark_outreach_sent, _conn

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "scraper", ".env"))

YOUR_NAME    = os.environ.get("YOUR_NAME", "Charles")
YOUR_EMAIL   = os.environ.get("YOUR_EMAIL", "")
FROM_ADDRESS = os.environ.get("FROM_ADDRESS", YOUR_EMAIL)

# SMTP (Gmail / Berkeley Google Workspace)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", YOUR_EMAIL)
SMTP_PASS = os.environ.get("SMTP_PASS", "")

# Resend fallback
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

TEMPLATES = {
    "cold":    Path(__file__).parent / "templates" / "cold_email.html",
    "follow1": Path(__file__).parent / "templates" / "follow_up_1.html",
    "follow2": Path(__file__).parent / "templates" / "follow_up_2.html",
}

FOLLOW_UP_DAYS = {"follow1": 4, "follow2": 10}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _ensure_columns() -> None:
    for sql in [
        "ALTER TABLE businesses ADD COLUMN owner_first_name TEXT",
        "ALTER TABLE businesses ADD COLUMN follow_up_1_sent_at TEXT",
        "ALTER TABLE businesses ADD COLUMN follow_up_2_sent_at TEXT",
    ]:
        try:
            with _conn() as c:
                c.execute(sql)
        except Exception:
            pass


def set_owner_email(place_id: str, email: str) -> None:
    with _conn() as c:
        c.execute("UPDATE businesses SET email = ? WHERE place_id = ?", (email, place_id))


def set_owner_name(place_id: str, name: str) -> None:
    with _conn() as c:
        c.execute("UPDATE businesses SET owner_first_name = ? WHERE place_id = ?", (name, place_id))


def mark_follow_up_sent(place_id: str, which: str) -> None:
    col = "follow_up_1_sent_at" if which == "follow1" else "follow_up_2_sent_at"
    with _conn() as c:
        c.execute(f"UPDATE businesses SET {col} = datetime('now') WHERE place_id = ?", (place_id,))


def get_businesses_due_for_followup(which: str) -> list[dict]:
    days = FOLLOW_UP_DAYS[which]
    sent_col = "follow_up_1_sent_at" if which == "follow1" else "follow_up_2_sent_at"
    prereq = (
        "outreach_sent = 1 AND responded = 0 AND email IS NOT NULL"
        + (" AND follow_up_1_sent_at IS NOT NULL" if which == "follow2" else "")
    )
    with _conn() as c:
        rows = c.execute(
            f"""SELECT * FROM businesses
                WHERE {prereq} AND {sent_col} IS NULL
                  AND outreach_sent_at <= datetime('now', '-{days} days')
                ORDER BY outreach_sent_at ASC""",
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def _render(template_key: str, business: dict) -> tuple[str, str]:
    template = TEMPLATES[template_key].read_text(encoding="utf-8")
    owner_name = business.get("owner_first_name") or None
    greeting = owner_name if owner_name else "team"

    html = (
        template
        .replace("{{BUSINESS_NAME}}", business["name"])
        .replace("{{FIRST_NAME_OR_TEAM}}", greeting)
        .replace("{{SITE_URL}}", business.get("site_url") or "#")
        .replace("{{YOUR_NAME}}", YOUR_NAME)
        .replace("{{YOUR_EMAIL}}", YOUR_EMAIL)
    )

    subjects = {
        "cold":    f"I made a website for {business['name']} - feedback?",
        "follow1": f"Re: website for {business['name']}",
        "follow2": f"Last note about the {business['name']} site",
    }
    return subjects[template_key], html


# ---------------------------------------------------------------------------
# Send backends
# ---------------------------------------------------------------------------

def _send_smtp(to_email: str, subject: str, html: str, from_name: str, from_addr: str) -> str:
    """Send via Gmail SMTP. Returns message ID on success, raises on failure."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{from_name} <{from_addr}>"
    msg["To"]      = to_email
    msg["Reply-To"] = from_addr
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(from_addr, [to_email], msg.as_bytes())

    return f"smtp-{to_email}-ok"


def _send_resend(to_email: str, subject: str, html: str, from_name: str, from_addr: str) -> str:
    """Send via Resend API. Returns message ID on success, raises on failure."""
    import resend as _resend
    _resend.api_key = RESEND_API_KEY
    params = {
        "from": f"{from_name} <{from_addr}>",
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    resp = _resend.Emails.send(params)
    msg_id = resp.get("id")
    if not msg_id:
        raise RuntimeError(f"Resend error: {resp}")
    return msg_id


# ---------------------------------------------------------------------------
# Main send orchestrator
# ---------------------------------------------------------------------------

def send_email(business: dict, template_key: str = "cold", dry_run: bool = False) -> bool:
    to_email = business.get("email")
    if not to_email:
        print(f"  No email for {business['name']} — skipping (run --set-email first)")
        return False

    subject, html = _render(template_key, business)

    if dry_run:
        print(f"\n{'='*60}")
        print(f"To:      {to_email}")
        print(f"From:    {YOUR_NAME} <{FROM_ADDRESS}>")
        print(f"Subject: {subject}")
        print(f"{'='*60}")
        sys.stdout.buffer.write(html.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
        return True

    # Choose backend
    if SMTP_PASS:
        backend = "SMTP"
        send_fn = lambda: _send_smtp(to_email, subject, html, YOUR_NAME, FROM_ADDRESS)
    elif RESEND_API_KEY:
        backend = "Resend"
        send_fn = lambda: _send_resend(to_email, subject, html, YOUR_NAME, FROM_ADDRESS)
    else:
        print("  ERROR: set SMTP_PASS (Gmail App Password) or RESEND_API_KEY in scraper/.env")
        return False

    try:
        msg_id = send_fn()
        if template_key == "cold":
            mark_outreach_sent(business["place_id"])
        else:
            mark_follow_up_sent(business["place_id"], template_key)
        print(f"  Sent [{template_key}] via {backend} -> {to_email}  ({msg_id})")
        return True
    except Exception as e:
        print(f"  ERROR [{backend}] sending to {to_email}: {e}")
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    _ensure_columns()

    parser = argparse.ArgumentParser()
    parser.add_argument("--list",      action="store_true")
    parser.add_argument("--preview",   metavar="PLACE_ID")
    parser.add_argument("--send",      metavar="PLACE_ID")
    parser.add_argument("--send-all",  action="store_true")
    parser.add_argument("--follow-ups",action="store_true")
    parser.add_argument("--set-email", nargs=2, metavar=("PLACE_ID", "EMAIL"))
    parser.add_argument("--set-name",  nargs=2, metavar=("PLACE_ID", "NAME"))
    args = parser.parse_args()

    if args.list:
        businesses = get_businesses_ready_for_outreach()
        no_email = [b for b in businesses if not b.get("email")]
        ready    = [b for b in businesses if b.get("email")]
        print(f"\n{len(ready)} ready to send ({len(no_email)} missing email):\n")
        for b in ready:
            print(f"  {b['name']}")
            print(f"    email: {b['email']}")
            print(f"    site:  {b.get('site_url', 'N/A')}\n")
        if no_email:
            print(f"{len(no_email)} need email enrichment:")
            for b in no_email:
                print(f"  {b['name']}  |  place_id: {b['place_id']}")

    elif args.set_email:
        place_id, email = args.set_email
        set_owner_email(place_id, email)
        print(f"Email set for {place_id}: {email}")

    elif args.set_name:
        place_id, name = args.set_name
        set_owner_name(place_id, name)
        print(f"Owner name set for {place_id}: {name}")

    elif args.preview:
        b = get_business(args.preview)
        if b:
            send_email(b, template_key="cold", dry_run=True)

    elif args.send:
        b = get_business(args.send)
        if b:
            send_email(b, template_key="cold")

    elif args.send_all:
        businesses = [b for b in get_businesses_ready_for_outreach() if b.get("email")]
        print(f"Sending to {len(businesses)} businesses...\n")
        for b in businesses:
            send_email(b, template_key="cold")

    elif args.follow_ups:
        for which in ("follow1", "follow2"):
            due = get_businesses_due_for_followup(which)
            label = "day-4 follow-up" if which == "follow1" else "day-10 close"
            print(f"\n{len(due)} businesses due for {label}:")
            for b in due:
                send_email(b, template_key=which)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""
Multi-channel outreach scripts for businesses without email addresses.

For the ~83 businesses where auto-enrichment found no email, this generates
ready-to-use scripts for the three working channels: phone call, GBP message, walk-in.

Usage:
    python channels.py --report                    # show all businesses by channel
    python channels.py --phone <place_id>          # print 30-sec phone script
    python channels.py --gbp <place_id>            # print GBP message to copy-paste
    python channels.py --walkin <place_id>         # print walk-in pitch
    python channels.py --set-channel <place_id> <email|gbp|phone|walkin>  # mark outreach channel
    python channels.py --mark-contacted <place_id> <channel>  # log outreach as sent
"""

import argparse
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scraper"))
from db import get_business, _conn

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "scraper", ".env"))

YOUR_NAME  = os.environ.get("YOUR_NAME", "Charles")
YOUR_EMAIL = os.environ.get("YOUR_EMAIL", "")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _ensure_columns() -> None:
    for sql in [
        "ALTER TABLE businesses ADD COLUMN outreach_channel TEXT",
        "ALTER TABLE businesses ADD COLUMN owner_first_name TEXT",
    ]:
        try:
            with _conn() as c:
                c.execute(sql)
        except Exception:
            pass


def get_all_with_sites() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM businesses WHERE site_built = 1 ORDER BY rating DESC NULLS LAST"
        ).fetchall()
        return [dict(r) for r in rows]


def set_channel(place_id: str, channel: str) -> None:
    with _conn() as c:
        c.execute("UPDATE businesses SET outreach_channel = ? WHERE place_id = ?", (channel, place_id))


def mark_contacted(place_id: str, channel: str) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE businesses SET outreach_sent = 1, outreach_sent_at = datetime('now'), outreach_channel = ? WHERE place_id = ?",
            (channel, place_id),
        )


# ---------------------------------------------------------------------------
# Script generators
# ---------------------------------------------------------------------------

def phone_script(b: dict) -> str:
    name = b["name"]
    url = b.get("site_url", "[DEMO URL]")
    phone = b.get("phone", "")
    return f"""
=== PHONE SCRIPT — {name} ===
Call: {phone}

"Hi, this is {YOUR_NAME}, I'm a UC Berkeley student.
I'm not selling anything right now — I actually built a sample website
for {name} over the weekend and I wanted to show you what it looks like.
Could I text you a link, or is there a better email to send it to?"

[If they say yes / give contact info]
-> Text or email: "{name} sample site: {url}"
-> Follow-up: "If you like it, $299 and it's yours — includes your own domain."

[If they say not interested]
-> "No problem at all — have a great day."

AFTER THE CALL:
  python send.py --set-email {b['place_id']} <email_they_gave>
  python channels.py --mark-contacted {b['place_id']} phone
"""


def gbp_message(b: dict) -> str:
    name = b["name"]
    url = b.get("site_url", "[DEMO URL]")
    return f"""
=== GBP MESSAGE — {name} ===
Open Google Maps -> search "{name} Berkeley" -> Message

--- COPY THIS ---
Hi! I'm a Cal student and I built a website for {name} using your
real photos from Google Maps: {url}

If you like it, $299 and it's yours. If not, no worries.
— {YOUR_NAME}
--- END ---

Character count: ~{len(f"Hi! I'm a Cal student and I built a website for {name} using your real photos from Google Maps: {url} If you like it, $299 and it's yours. If not, no worries. — {YOUR_NAME}")} / 1000 limit

AFTER SENDING:
  python channels.py --mark-contacted {b['place_id']} gbp
"""


def walkin_script(b: dict) -> str:
    name = b["name"]
    url = b.get("site_url", "[DEMO URL]")
    phone = b.get("phone", "")
    address = b.get("address", "")
    return f"""
=== WALK-IN PITCH — {name} ===
Address: {address}
Phone: {phone}
Demo: {url}

PREP: load {url} on your phone before walking in.

"Hi — quick non-[product] question. I'm a Cal student and I built a
polished website for {name} over the weekend, just to show you what's
possible. Could I show you on my phone for 30 seconds? If you like it,
$299 and it's yours; if not, no worries at all."

[Show them the demo on your phone]

[If interested]
-> Ask for email or phone to send the link
-> "I'll send you the link and a Stripe payment page — takes 5 minutes."

[If not interested]
-> "Totally fine — thanks for looking!" (Don't push.)

AFTER:
  python send.py --set-email {b['place_id']} <email_if_given>
  python channels.py --mark-contacted {b['place_id']} walkin
"""


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def channel_report() -> None:
    businesses = get_all_with_sites()
    email_ready = [b for b in businesses if b.get("email") and not b.get("outreach_sent")]
    no_email = [b for b in businesses if not b.get("email") and not b.get("outreach_sent")]
    sent = [b for b in businesses if b.get("outreach_sent")]

    print(f"\n{'='*60}")
    print(f"OUTREACH PIPELINE — {len(businesses)} businesses with sites")
    print(f"{'='*60}")

    print(f"\n[EMAIL READY — {len(email_ready)} businesses]")
    print("  Run: python send.py --send <place_id>")
    for b in email_ready:
        print(f"  {b['name']}")
        print(f"    email: {b['email']}")
        print(f"    place_id: {b['place_id']}")

    print(f"\n[NEEDS CHANNEL OUTREACH — {len(no_email)} businesses]")
    print("  Run: python channels.py --phone/--gbp/--walkin <place_id>")
    for b in no_email[:20]:
        phone = b.get("phone") or "no phone"
        ch = b.get("outreach_channel") or "not set"
        print(f"  {b['name']:<40}  {phone:<18}  channel={ch}")
    if len(no_email) > 20:
        print(f"  ... and {len(no_email) - 20} more")

    print(f"\n[ALREADY CONTACTED — {len(sent)} businesses]")
    for b in sent:
        ch = b.get("outreach_channel") or "email"
        resp = "REPLIED" if b.get("responded") else "no reply yet"
        sold = " SOLD $" + str(b.get("sale_amount", "")) if b.get("sold") else ""
        print(f"  {b['name']}  [{ch}]  {resp}{sold}")

    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    _ensure_columns()

    parser = argparse.ArgumentParser()
    parser.add_argument("--report",        action="store_true")
    parser.add_argument("--phone",         metavar="PLACE_ID")
    parser.add_argument("--gbp",           metavar="PLACE_ID")
    parser.add_argument("--walkin",        metavar="PLACE_ID")
    parser.add_argument("--set-channel",   nargs=2, metavar=("PLACE_ID", "CHANNEL"))
    parser.add_argument("--mark-contacted",nargs=2, metavar=("PLACE_ID", "CHANNEL"))
    args = parser.parse_args()

    if args.report:
        channel_report()
    elif args.phone:
        b = get_business(args.phone)
        print(phone_script(b) if b else f"Not found: {args.phone}")
    elif args.gbp:
        b = get_business(args.gbp)
        print(gbp_message(b) if b else f"Not found: {args.gbp}")
    elif args.walkin:
        b = get_business(args.walkin)
        print(walkin_script(b) if b else f"Not found: {args.walkin}")
    elif args.set_channel:
        place_id, channel = args.set_channel
        set_channel(place_id, channel)
        print(f"Channel set: {place_id} -> {channel}")
    elif args.mark_contacted:
        place_id, channel = args.mark_contacted
        mark_contacted(place_id, channel)
        print(f"Marked contacted: {place_id} via {channel}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

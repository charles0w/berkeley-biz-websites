# berkeley-biz-websites

Automated pipeline: scrape local businesses near UC Berkeley without websites → generate aesthetically pleasing sites using Google Maps photos + Claude copy → cold-email them offering to sell the site.

## Pipeline stages

```
scraper/scrape.py  →  data/businesses.db  →  dashboard (localhost:8080)  →  Vercel + Resend
```

1. **Scrape** — `cd scraper && python scrape.py` — runs once to populate the DB
2. **Generate** — `cd generator && python generate.py <place_id>` — builds + deploys site to Vercel
3. **Enrich emails** — `cd scraper && python enrich_emails.py --run` — auto-finds owner emails
4. **Set email manually** — `cd outreach && python send.py --set-email <place_id> <email>`
5. **Preview** — `cd outreach && python send.py --preview <place_id>` — verify email without sending
6. **Send** — `cd outreach && python send.py --send <place_id>` — send to one business
7. **Send all** — `cd outreach && python send.py --send-all` — send to all with emails set
8. **Follow-ups** — `cd outreach && python send.py --follow-ups` — send day-4 and day-10 follow-ups

## Multi-channel outreach (for the 83 without email)

Most small local businesses have no public email — DDG/Yelp enrichment found 0/83. Use the channel scripts:

```bash
cd outreach
python channels.py --report                          # see all businesses by channel
python channels.py --gbp <place_id>                  # GBP message to copy-paste
python channels.py --phone <place_id>                # 30-sec phone script
python channels.py --walkin <place_id>               # walk-in pitch
python channels.py --mark-contacted <place_id> gbp   # log after sending
```

After they give you an email (via phone/walk-in):
```bash
python send.py --set-email <place_id> their@email.com
python send.py --send <place_id>
```

## Current state (2026-05-27)

- **85 businesses** in DB, all with sites deployed to Vercel
- **2 ready to send:** Royal Ground Coffee, La Petite Hair Salon
- **83 need email enrichment** — enrichment script running/ran: `python enrich_emails.py --run`
- **0 sent so far**

## ONE THING NEEDED TO SEND

Add your Gmail App Password to `scraper/.env`:

1. Go to: **myaccount.google.com → Security → 2-Step Verification → App passwords**
2. Create an app password named "Berkeley Biz Websites"
3. Copy the 16-character password
4. Paste it in `scraper/.env` as: `SMTP_PASS=xxxx xxxx xxxx xxxx`

Then send the first email:
```bash
cd outreach
python send.py --send ChIJjZYlxYJ-hYARgM4953brw1U   # Royal Ground Coffee
```

## Phase 0 cohort

| Business | place_id | Email | Channel |
|---|---|---|---|
| Royal Ground Coffee | ChIJjZYlxYJ-hYARgM4953brw1U | chung@royalgroundcoffee.com | email |
| La Petite Hair Salon | ChIJHxep3Sd8hYARKGKuKac5t8A | lan@lapetitehair.com | email |
| Polished Nail Spa | ChIJLcHWep9-hYARxFcvSE-IDlY | GBP message | GBP |
| Caravaggio Gelato Lab | ChIJlfhgeZ9-hYARwZHnZ5wFnI0 | walk-in or phone | walk-in |
| Gadani | ChIJGX6R051-hYARhCF3ijh0Dt8 | GBP fallback | GBP/email |

## Key files

| File | Purpose |
|---|---|
| `scraper/scrape.py` | Google Maps Places API scraper |
| `scraper/db.py` | SQLite layer — all pipeline state lives here |
| `scraper/enrich_emails.py` | Auto-find owner emails via DDG + Yelp |
| `generator/generate.py` | Site generation + Vercel deploy |
| `generator/copy_writer.py` | Claude Haiku copy generation (tagline + about) |
| `outreach/send.py` | Cold email via Gmail SMTP (primary) or Resend (fallback) |
| `outreach/templates/cold_email.html` | Cold email template |
| `outreach/templates/follow_up_1.html` | Day-4 follow-up (discounted at $249) |
| `outreach/templates/follow_up_2.html` | Day-10 final close |
| `data/businesses.db` | SQLite database (gitignored) |

## Reply handling (when someone says yes)

1. Reply within 2 hours: *"Awesome — I'll send the Stripe link in this thread within 30 minutes."*
2. Create a Stripe payment link for $299 at dashboard.stripe.com
3. After payment: transfer the Vercel project + buy/transfer their domain
4. Log sale in DB: `python send.py --set-email <place_id> <status>` then update `sold=1` manually

## Legal notes

- Google Maps photos: currently downloaded at generation time for static hosting — review TOS before selling at scale
- Cold email: CAN-SPAM compliant template — keep the footer
- No Instagram DM automation — violates ToS

## Second brain

This project is indexed in the Obsidian vault at:
`C:\Users\charl\Desktop\obi-secondbrain\repos\berkeley-biz-websites\`

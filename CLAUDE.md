# berkeley-biz-websites

Automated pipeline: scrape local businesses near UC Berkeley without websites → generate aesthetically pleasing sites using Google Maps photos + Claude copy → cold-email them offering to sell the site.

## Pipeline stages

```
scraper/scrape.py  →  data/businesses.db  →  dashboard (localhost:8080)  →  Vercel + Resend
```

1. **Scrape** — `cd scraper && python scrape.py` — runs once to populate the DB
2. **Dashboard** — `dashboard/start.bat` — control center for everything else:
   - Click "Generate Site" per business → builds + deploys to Vercel
   - Enter owner email → "Preview Email" → "Approve & Send" → goes via Resend
   - Track status: Scraped → Building → Ready → Sent → Responded → Sold

## Key files

| File | Purpose |
|---|---|
| `scraper/scrape.py` | Google Maps Places API scraper |
| `scraper/db.py` | SQLite layer — all pipeline state lives here |
| `generator/generate.py` | Site generation + Vercel deploy |
| `generator/copy_writer.py` | Claude Haiku copy generation (tagline + about) |
| `outreach/email.py` | Cold email via Resend |
| `outreach/templates/cold_email.html` | Email template (edit the pitch here) |
| `site-template/` | Next.js 14 + Tailwind site (static export) |
| `site-template/business.json` | Single source of truth for each generated site |
| `data/businesses.db` | SQLite database (gitignored) |

## Setup

```bash
# 1. Copy and fill in the env file
cp scraper/.env.example scraper/.env

# 2. Install Python deps
pip install -r scraper/requirements.txt
# Also add: anthropic resend (for generator + outreach)

# 3. Install Node deps for the site template
cd site-template && npm install

# 4. Install Vercel CLI
npm i -g vercel && vercel login
```

## Data model (businesses.db)

Pipeline state columns: `site_built`, `site_url`, `outreach_sent`, `outreach_sent_at`, `responded`, `sold`, `sale_amount`.

## Legal notes

- Google Maps photos: currently downloaded at generation time for static hosting — review TOS before selling sites at scale
- Cold email: CAN-SPAM compliant template in `outreach/templates/cold_email.html` — keep the footer
- No Instagram DM automation — violates ToS

## Second brain

This project is indexed in the Obsidian vault at:
`C:\Users\charl\Desktop\obi-secondbrain\projects\berkeley-biz-websites\overview.md`

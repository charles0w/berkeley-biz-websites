 # BerkeleyBiz — Autonomous B2B Outreach Pipeline

  Scrapes local business listings, generates a custom website landing page
  for each prospect, and fires personalized cold emails — zero human steps
  between discovery and outreach.

  ## How it works

  | Stage | What happens |
  |---|---|
  | **Scrape** | Discovers businesses, pulls contact info + web presence signals |
  | **Enrich** | Runs data through the pipeline to score and filter prospects |
  | **Generate** | Builds a custom landing page mockup using the prospect's brand data |
  | **Outreach** | Sends a personalized cold email with the generated site as the hook |
  | **Report** | `ceo_report.py` produces an executive summary of pipeline performance |

  ## Stack

  - **Python** — scraper, pipeline orchestration, outreach automation
  - **TypeScript** — site template generation and rendering
  - **Supabase** — prospect database and pipeline state
  - **GitHub Actions** — scheduled pipeline runs and CI

  ## Architecture

  BerkeleyBiz/
  ├── scraper/          # Business discovery & contact enrichment
  ├── pipeline/         # Orchestration, filtering, scoring
  ├── generator/        # Custom site/content generation per prospect
  ├── site-template/    # Landing page templates
  ├── outreach/         # Email automation
  ├── data/             # Persistent storage layer
  └── ceo_report.py     # Pipeline analytics & performance reporting

  ## Why the approach works

  Generic cold email gets ignored. This pipeline creates a tangible,
  personalized artifact — a website built specifically for the prospect —
  before contact is made. The conversion hook is concrete, not a pitch.

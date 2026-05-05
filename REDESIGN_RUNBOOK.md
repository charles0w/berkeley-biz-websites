# Site Template Redesign — Runbook (2026-04-29)

The `site-template/` was rewritten end-to-end against a stack of design skills
that explicitly ban the AI-default look (Inter font, generic dark-overlay heroes,
heavy drop shadows, `h-screen` mobile bug). Every existing generated site under
`generated/` is still on the OLD template. This runbook walks through validating
the new template and rolling it out across all 78 already-built sites.

## What changed (in `site-template/`)

| File | Change |
|---|---|
| `tailwind.config.ts` | Inter → Plus Jakarta Sans; Cormorant → Newsreader; added cream/espresso/sage/mute palette; ambient low-opacity shadows; no rounded-full pills. |
| `app/globals.css` | Newsreader + Plus Jakarta Sans + JetBrains Mono via Google Fonts; subtle SVG paper-grain overlay; `.reveal` scroll-in; `.hairline` divider; `.press` button feedback. |
| `app/layout.tsx` | Adds `viewport-fit=cover` and `themeColor` for proper iOS Safari notch + status-bar handling. |
| `app/page.tsx` | New section order: Nav → Hero → About → Gallery → Hours → Contact → Footer; mounts `<StickyCallCTA />` and `<Reveal />`. |
| `components/Hero.tsx` | Editorial-Luxury archetype. Asymmetric two-column. No `h-screen` (mobile fix). No dark gradient overlay. Tap-to-call primary CTA. Layered photo treatment. |
| `components/Nav.tsx` | Removed scrolled/unscrolled state switch. Tap-to-call always visible (mobile + desktop). |
| `components/About.tsx` | Asymmetric 5/7 split. Heading uses actual business category, not "institution". Rating block redesigned. |
| `components/Hours.tsx` | Mono day-times, hairline dividers, asymmetric 4/8 split, real CTA button on Google Maps. |
| `components/Gallery.tsx` | `<img>` + `aspect-*` instead of background-image divs; `photo-warm` filter masks raw Google photo variance; asymmetric bento; supports up to 4 photos. |
| `components/Contact.tsx` | 5/7 split, embedded Google Maps iframe (no API key needed), tap-to-call primary in espresso. |
| `components/Footer.tsx` | Hairline divider, mono address line, "sample site" disclaimer. |
| `components/StickyCallCTA.tsx` | NEW. Mobile-only sticky tap-to-call FAB; visible after scroll past 380px. |
| `components/Reveal.tsx` | NEW. Global IntersectionObserver that adds `.in` to all `.reveal` elements as they enter the viewport. Honors `prefers-reduced-motion`. |

## Validation gate (do these in order)

### 1. Local dev preview against one generated site (5 min)

The fastest way to see the new design is to point a single existing
generated site at the new template and run `next dev`:

```powershell
# From the repo root
cd site-template
npm install                              # if node_modules is missing
npm run dev                              # http://localhost:3000

# In a separate terminal — copy a real generated business.json + photos
# in so you preview against a real business, not the placeholder:
$src = "..\generated\ChIJ-Tg5WoJ-hYARfAk0G-bLNaI"   # any place_id
copy $src\business.json business.json
copy $src\public\images\* public\images\
```

Then open http://localhost:3000 and run the **10-second test** from
`obi-secondbrain/repos/berkeley-biz-websites/sellable-website-checklist.md`:

- [ ] Real business name spelled correctly, in the hero
- [ ] Real photos load (not placeholder cream blocks)
- [ ] Hours table reads correctly
- [ ] Tap-to-call works on a phone (test with browser dev-tools mobile view + actual phone)
- [ ] Mobile sticky FAB appears after scrolling past hero
- [ ] No layout jump on iOS Safari (the `min-h-[100dvh]` fix)
- [ ] Loads in <1 second on cellular throttling (Chrome DevTools → Network → Slow 3G)
- [ ] No browser console errors

### 2. TypeScript pass (1 min)

```powershell
cd site-template
npx tsc --noEmit
```

Should print nothing (zero errors). If TS fails, fix before continuing.

### 3. Production build smoke test (3 min)

```powershell
cd site-template
npx next build
```

Should produce a clean `.next/` and `out/` directory. Static export means
no server is needed for any deployed site.

### 4. Single-site deploy smoke test (5 min)

Pick ONE existing place_id and redeploy it via the helper script:

```powershell
cd ..
python generator/redeploy_all.py ChIJ-Tg5WoJ-hYARfAk0G-bLNaI
```

Open the resulting Vercel URL on a phone. Confirm everything from the
10-second test still passes when deployed (CDN, cellular, real device).
**Only proceed past this gate if the live URL passes.**

### 5. Limit-3 batch (10 min)

Run on 3 sites to make sure batching works:

```powershell
python generator/redeploy_all.py --limit 3
```

Each one should complete cleanly. Open all 3 live URLs on a phone.

### 6. Full batch (30-60 min)

Once 1, 2, 3 all look good, run the full re-deploy:

```powershell
python generator/redeploy_all.py
```

The script copies the new template files into each `generated/<place_id>/`
directory (preserving `business.json` and `public/images/`) and runs
`vercel --prod` per site. Output prints success/failure per site.

**No Claude API spend, no Google Photo API spend, no Maps API spend.**
Only Vercel build minutes.

### 7. Spot-check 10 sites (5 min)

Open 10 of the live URLs on your phone. Look for layout breakage on
edge-case data (very long names, missing rating, no gallery photos,
unusual hour formats, etc.). Note any specific business that breaks
in `obi-secondbrain/repos/berkeley-biz-websites/notes.md` so the
template can be hardened in the next pass.

## Rollback (if something is wrong)

The new `site-template/` is in `git`. To revert:

```powershell
git -C C:\Users\charl\Desktop\berkeley-biz-websites diff HEAD site-template/
git -C C:\Users\charl\Desktop\berkeley-biz-websites checkout HEAD -- site-template/
python generator/redeploy_all.py    # re-deploy everyone with the old template
```

Costs: 30-60 min of Vercel build time. No API spend.

## What `redeploy_all.py` does (reference)

1. Iterates over every directory in `generated/` that has a `business.json`.
2. For each one, copies these files from `site-template/` over the existing
   site's copy (overwriting the old template files):
   - `app/{globals.css,layout.tsx,page.tsx}`
   - `components/{*.tsx}` — every component file
   - `lib/business.ts`
   - `tailwind.config.ts`, `postcss.config.js`, `tsconfig.json`, `next.config.js`
   - `package.json`, `package-lock.json` (in case dependencies changed)
3. Leaves `business.json` and `public/images/*` alone — those are per-site data.
4. Runs `npx vercel --yes --prod --name <slug>` per site.
5. Reports successes and failures at the end.

Useful flags:
- `--dry-run` — prints the list, doesn't change anything
- `--limit N` — only the first N sites (smoke test)
- `--no-deploy` — sync files but skip the Vercel call (useful to inspect locally)
- `<place_id>` (positional) — only that one site

## When to use `redeploy_all.py` vs `generate.py all`

| Situation | Use |
|---|---|
| You only changed `site-template/` design | **`redeploy_all.py`** — fast, free, no API spend |
| You changed `copy_writer.py` (Claude prompt) | `generate.py all` — needs to re-run Claude per business |
| Photos are wrong / out of date | `generate.py <place_id>` per business — re-pulls from Places Photo API |
| New scrape, new businesses | `generate.py <place_id>` for each new one |

## Cost expectations

- `redeploy_all.py` for 78 sites: **$0 in API spend, ~30-60 min wall-clock**
- `generate.py all` for 78 sites: **~$0.30 in Claude Haiku + ~$15 in Google Photo API + same Vercel time**

## Skills referenced (in `obi-secondbrain/.claude/skills/`)

- `impeccable` — design discipline / critique pass
- `huashu-design` — hi-fi prototype variants
- `ui-ux-pro-max` — per-stack reference data
- `design-taste-frontend` — VARIANCE/MOTION/DENSITY tokens, anti-pattern bans
- `high-end-visual-design` — archetype B (Editorial Luxury) for cafes/salons
- `minimalist-ui` — banned-defaults list (Inter, Roboto, Lucide, shadow-md, gradients)
- `full-output-enforcement` — anti-truncation discipline; no `// rest of code` placeholders
- `brandkit` — premium brand-kit composition logic (used as inspiration; not invoked at runtime)

For the next iteration round (after smoke-test data comes in), invoke
the skills directly inside Claude Code to do a critique pass:

```
> read .claude/skills/impeccable/SKILL.md and run a design critique pass on
> site-template/ — flag anything that violates the rules in that skill or
> in .claude/skills/minimalist-ui/SKILL.md
```

## See also

- `obi-secondbrain/repos/berkeley-biz-websites/sellable-website-checklist.md` — the 10-second test
- `obi-secondbrain/repos/berkeley-biz-websites/photo-rights.md` — production photo strategy
- `obi-secondbrain/repos/berkeley-biz-websites/cold-email-drafts-2026-04-28.md` — cold-email v1 to send once Phase 0 cohort demos are live

"""
Re-deploy all existing generated sites against the current site-template/
WITHOUT re-running Claude copy or re-downloading photos.

Use this AFTER editing site-template/ when you want every previously-built
site to pick up the new design without burning more API spend.

Cost: zero API calls. Only Vercel build minutes.
Time: ~30-60 sec per site, sequential. With 78 sites that's ~30-60 min.

Usage:
    python generator/redeploy_all.py             # redeploy ALL sites in generated/
    python generator/redeploy_all.py --dry-run   # show what would happen, don't deploy
    python generator/redeploy_all.py --limit 3   # smoke test on the first 3
    python generator/redeploy_all.py <place_id>  # redeploy a single site
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "site-template"
GENERATED_DIR = ROOT / "generated"

# Files / dirs from site-template/ that are SHARED structure and must overwrite
# every generated site. business.json + public/images stay per-site.
SYNC_FILES = [
    "app/globals.css",
    "app/layout.tsx",
    "app/page.tsx",
    "components/About.tsx",
    "components/Contact.tsx",
    "components/Footer.tsx",
    "components/Gallery.tsx",
    "components/Hero.tsx",
    "components/Hours.tsx",
    "components/Nav.tsx",
    "components/Reveal.tsx",
    "components/StickyCallCTA.tsx",
    "lib/business.ts",
    "tailwind.config.ts",
    "postcss.config.js",
    "tsconfig.json",
    "next.config.js",
    "package.json",
    "package-lock.json",
]


def sync_template_into(site_dir: Path) -> None:
    """Copy structural template files into a generated site directory, leaving
    business.json + public/images alone."""
    for rel in SYNC_FILES:
        src = TEMPLATE_DIR / rel
        dst = site_dir / rel
        if not src.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(src, dst)


def deploy(site_dir: Path) -> str | None:
    """Run `vercel --prod` for an already-existing project; return URL or None."""
    name = site_dir.name.replace("_", "-").lower()
    cmd = "npx vercel --yes --prod"
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=str(site_dir), capture_output=True, text=True, timeout=600
        )
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: vercel deploy took >10 min for {site_dir.name}")
        return None

    out = (result.stdout or "") + (result.stderr or "")
    for line in out.splitlines():
        line = line.strip()
        # Output format: "Production: https://... [Xs]" or "Aliased: https://..."
        for token in line.split():
            if token.startswith("https://") and "vercel.app" in token:
                return token
    return None


def list_sites(limit: int | None) -> list[Path]:
    if not GENERATED_DIR.exists():
        return []
    sites = sorted(d for d in GENERATED_DIR.iterdir() if d.is_dir())
    if limit is not None:
        sites = sites[:limit]
    return sites


def has_business_json(site_dir: Path) -> bool:
    return (site_dir / "business.json").is_file()


def biz_name(site_dir: Path) -> str:
    bj = site_dir / "business.json"
    if bj.is_file():
        try:
            return json.loads(bj.read_text()).get("name", site_dir.name)
        except Exception:
            return site_dir.name
    return site_dir.name


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("place_id", nargs="?", help="If set, only redeploy this site.")
    ap.add_argument("--dry-run", action="store_true", help="Show what would happen.")
    ap.add_argument("--limit", type=int, help="Only the first N sites.")
    ap.add_argument("--no-deploy", action="store_true", help="Sync files but skip Vercel deploy.")
    args = ap.parse_args()

    if args.place_id:
        targets = [GENERATED_DIR / args.place_id]
    else:
        targets = list_sites(args.limit)

    targets = [d for d in targets if d.exists() and has_business_json(d)]

    if not targets:
        print("Nothing to do — no generated sites found.")
        return

    print(f"\n{len(targets)} site(s) to redeploy:\n")
    for t in targets:
        print(f"  - {biz_name(t)}  ({t.name})")
    print()

    if args.dry_run:
        print("Dry run — not changing anything.")
        return

    successes: list[tuple[str, str]] = []
    failures: list[tuple[str, str]] = []

    for i, site_dir in enumerate(targets, 1):
        name = biz_name(site_dir)
        print(f"\n[{i}/{len(targets)}] {name}")
        print(f"  Syncing template files…")
        sync_template_into(site_dir)
        if args.no_deploy:
            successes.append((name, "synced (no deploy)"))
            continue
        print(f"  Deploying…")
        url = deploy(site_dir)
        if url:
            print(f"  OK: {url}")
            successes.append((name, url))
        else:
            print(f"  ERROR: deploy returned no URL")
            failures.append((name, "deploy failed"))
        time.sleep(0.5)  # gentle pace, not strictly required

    print("\n" + "=" * 60)
    print(f"Done. {len(successes)} succeeded, {len(failures)} failed.")
    if failures:
        print("\nFailures:")
        for name, reason in failures:
            print(f"  - {name}: {reason}")


if __name__ == "__main__":
    main()

"""
Generate and deploy a site for one business.

Usage:
    cd generator
    python generate.py <place_id>          # generate + deploy
    python generate.py <place_id> --build-only  # generate but don't deploy (for testing)
    python generate.py --list              # list all businesses in DB
"""
from __future__ import annotations
import os
import sys
import json
import shutil
import subprocess
import tempfile
import argparse
import requests
import urllib.request
import urllib.parse
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'scraper', '.env'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scraper'))

from db import Database
from copy_writer import generate_copy

SITE_TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'site-template'))
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
VERCEL_TOKEN = os.environ.get('VERCEL_TOKEN', '')


def download_photos(photo_refs: list, slug: str, max_photos: int = 5) -> list[str]:
    photos_dir = os.path.join(SITE_TEMPLATE_DIR, 'public', 'images')
    os.makedirs(photos_dir, exist_ok=True)

    saved = []
    for i, ref in enumerate(photo_refs[:max_photos]):
        url = (
            f"https://maps.googleapis.com/maps/api/place/photo"
            f"?maxwidth=1200&photo_reference={ref}&key={GOOGLE_MAPS_API_KEY}"
        )
        try:
            resp = requests.get(url, allow_redirects=True, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f'  photo {i} download failed: {e}')
            continue

        filename = f"{slug}-{i}.jpg"
        filepath = os.path.join(photos_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(resp.content)
        saved.append(f"images/{filename}")
        print(f'  downloaded photo {i+1}/{min(len(photo_refs), max_photos)}')

    return saved


def build_site(biz: dict, work_dir: str):
    """Write business.json and build the Next.js static export in work_dir."""
    hours = json.loads(biz.get('hours_json') or '{}')
    photos = json.loads(biz.get('_local_photos') or '[]')

    business_data = {
        'name': biz['name'],
        'slug': biz['slug'],
        'tagline': biz['_tagline'],
        'about': biz['_about'],
        'phone': biz.get('phone') or '',
        'address': biz.get('address') or '',
        'hours': hours,
        'category': biz.get('category') or 'services',
        'rating': biz.get('rating') or 0,
        'review_count': biz.get('review_count') or 0,
        'photos': photos,
        'place_id': biz['place_id'],
    }

    with open(os.path.join(work_dir, 'business.json'), 'w') as f:
        json.dump(business_data, f, indent=2, default=lambda x: float(x) if isinstance(x, Decimal) else str(x))

    # Copy downloaded photos into the work dir
    dest_images = os.path.join(work_dir, 'public', 'images')
    os.makedirs(dest_images, exist_ok=True)
    src_images = os.path.join(SITE_TEMPLATE_DIR, 'public', 'images')
    for photo_rel in photos:
        src = os.path.join(SITE_TEMPLATE_DIR, 'public', photo_rel)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(work_dir, 'public', photo_rel.replace('images/', '')))

    # npm install (only if node_modules missing)
    if not os.path.exists(os.path.join(work_dir, 'node_modules')):
        print('  npm install...')
        subprocess.run(['npm', 'install', '--prefer-offline'], cwd=work_dir,
                       check=True, capture_output=True)

    print('  next build...')
    result = subprocess.run(['npm', 'run', 'build'], cwd=work_dir,
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-2000:])
        raise RuntimeError('Next.js build failed')


def deploy_to_vercel(work_dir: str, project_name: str) -> str:
    # Write vercel.json with project name (--name flag deprecated in CLI v39+)
    vercel_cfg = os.path.join(work_dir, 'vercel.json')
    existing = {}
    if os.path.exists(vercel_cfg):
        with open(vercel_cfg) as f:
            import json as _json
            try:
                existing = _json.load(f)
            except Exception:
                pass
    existing['name'] = project_name
    with open(vercel_cfg, 'w') as f:
        import json as _json
        _json.dump(existing, f)

    vercel_bin = os.path.expanduser('~/.local/bin/vercel')
    if not os.path.exists(vercel_bin):
        vercel_bin = 'vercel'

    result = subprocess.run(
        [vercel_bin, '--prod', '--yes', '--no-wait',
         '--scope', 'charles-ows-projects', '--token', VERCEL_TOKEN],
        cwd=work_dir,
        capture_output=True, text=True,
    )
    # --no-wait: Vercel returns 0 once the deployment is queued.
    # ECONNRESET during polling is also non-fatal since the build runs on Vercel.
    if result.returncode != 0:
        # Surface the error but treat ECONNRESET as a likely success
        if 'ECONNRESET' in result.stdout or 'ECONNRESET' in result.stderr:
            print('  (ECONNRESET during poll — deployment queued, using deterministic URL)')
        else:
            print('STDOUT:', result.stdout[-1000:])
            print('STDERR:', result.stderr[-1000:])
            raise RuntimeError('Vercel deploy failed')

    # Try to extract the production URL from CLI output
    for line in result.stdout.splitlines() + result.stderr.splitlines():
        line = line.strip()
        if line.startswith('Production:'):
            url = line.split('Production:', 1)[-1].strip().split()[0]
            if url.startswith('https://'):
                return url
    for line in reversed(result.stdout.splitlines()):
        line = line.strip()
        if line.startswith('https://') and 'vercel.app' in line:
            return line

    # Deterministic production URL — always <project-name>.vercel.app
    return f'https://{project_name}.vercel.app'


CUSTOM_DOMAIN_BASE = os.environ.get('CUSTOM_DOMAIN_BASE', 'charlesbuilds.online')
VERCEL_TEAM_ID = 'team_WRCzWKnhfhGQBzZTMmji0lSj'


def assign_custom_domain(slug: str) -> str | None:
    """Add {slug}.charlesbuilds.online as an alias to the Vercel project.
    Requires wildcard CNAME *.charlesbuilds.online → cname.vercel-dns.com in DNS."""
    if not VERCEL_TOKEN or not CUSTOM_DOMAIN_BASE:
        return None
    subdomain = f'{slug}.{CUSTOM_DOMAIN_BASE}'
    project_name = f'biz-{slug}'
    url = (
        f'https://api.vercel.com/v9/projects/{project_name}/domains'
        f'?teamId={VERCEL_TEAM_ID}'
    )
    payload = json.dumps({'name': subdomain}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            'Authorization': f'Bearer {VERCEL_TOKEN}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        if data.get('name') == subdomain or data.get('verified'):
            return f'https://{subdomain}'
        # Already exists is fine too
        if 'already' in str(data).lower() or data.get('error', {}).get('code') == 'domain_already_in_use':
            return f'https://{subdomain}'
        print(f'  domain API response: {data}')
        return f'https://{subdomain}'  # optimistically return it anyway
    except Exception as e:
        print(f'  custom domain assignment failed: {e}')
        return None


def fetch_extra_photo_refs(place_id: str, existing_refs: list, target: int = 8) -> list:
    """Fetch additional photo_refs from Places Details API if we have fewer than target."""
    if len(existing_refs) >= target or not GOOGLE_MAPS_API_KEY:
        return existing_refs
    try:
        qs = urllib.parse.urlencode({
            'place_id': place_id,
            'fields': 'photos',
            'key': GOOGLE_MAPS_API_KEY,
        })
        url = 'https://maps.googleapis.com/maps/api/place/details/json?' + qs
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        api_refs = [
            p['photo_reference']
            for p in data.get('result', {}).get('photos', [])
            if 'photo_reference' in p
        ]
        # Merge, preserving order, deduplicating
        seen = set(existing_refs)
        merged = list(existing_refs)
        for ref in api_refs:
            if ref not in seen:
                merged.append(ref)
                seen.add(ref)
        print(f'  fetched {len(api_refs)} photo refs from API → {len(merged)} total')
        return merged[:target]
    except Exception as e:
        print(f'  photo ref fetch skipped: {e}')
        return existing_refs


def generate_site(place_id: str, build_only: bool = False) -> str:
    db = Database()
    biz = db.get_business(place_id)
    if not biz:
        sys.exit(f'Business not found: {place_id}')

    print(f'\nGenerating: {biz["name"]}')

    # 1. Download photos — fetch extra refs from API if < 3 stored
    photo_refs = json.loads(biz.get('photo_refs') or '[]')
    photo_refs = fetch_extra_photo_refs(place_id, photo_refs, target=8)
    photos = download_photos(photo_refs, biz['slug'], max_photos=8)
    biz['_local_photos'] = json.dumps(photos)

    # 2. Generate copy
    print('  generating copy with Claude Haiku...')
    copy = generate_copy(biz)
    biz['_tagline'] = copy['tagline']
    biz['_about'] = copy['about']
    print(f'  tagline: {copy["tagline"]}')

    # 3. Copy template to temp dir
    work_dir = tempfile.mkdtemp(prefix=f'biz-{biz["slug"]}-')
    shutil.copytree(SITE_TEMPLATE_DIR, work_dir, dirs_exist_ok=True)

    # 4. Build
    build_site(biz, work_dir)

    if build_only:
        print(f'\nBuild complete. Static export at: {work_dir}/out/')
        return work_dir

    # 5. Deploy
    project_name = f'biz-{biz["slug"]}'
    print(f'  deploying to Vercel as {project_name}...')
    url = deploy_to_vercel(work_dir, project_name)

    # 6. Assign custom subdomain (requires wildcard DNS in place)
    custom_url = assign_custom_domain(biz['slug'])
    if custom_url:
        print(f'  custom domain: {custom_url}')
        url = custom_url

    # 7. Persist
    db.update_business(place_id, demo_url=url, status='generated')
    shutil.rmtree(work_dir, ignore_errors=True)

    print(f'\nDone. Live at: {url}')
    return url


def list_businesses():
    db = Database()
    rows = db.get_all()
    if not rows:
        print('No businesses in DB yet. Run scraper/scrape.py first.')
        return
    print(f'{"Place ID":<30} {"Name":<40} {"Status":<12} Demo URL')
    print('-' * 110)
    for b in rows:
        print(f'{b["place_id"]:<30} {b["name"]:<40} {(b["status"] or ""):<12} {b.get("demo_url") or ""}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('place_id', nargs='?', help='Google place_id to generate')
    parser.add_argument('--build-only', action='store_true', help='Build but do not deploy to Vercel')
    parser.add_argument('--list', action='store_true', help='List all businesses in DB')
    args = parser.parse_args()

    if args.list:
        list_businesses()
    elif args.place_id:
        generate_site(args.place_id, build_only=args.build_only)
    else:
        parser.print_help()

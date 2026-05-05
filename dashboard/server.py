"""
Dashboard server for the Berkeley Biz Websites pipeline.

Run:  uvicorn server:app --reload --port 8080
Then open: http://localhost:8080
"""

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import resend
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / "scraper" / ".env")

sys.path.insert(0, str(ROOT / "scraper"))
import db as DB

DB.init_db()

resend.api_key = os.environ.get("RESEND_API_KEY", "")
YOUR_NAME  = os.environ.get("YOUR_NAME", "Charles")
YOUR_EMAIL = os.environ.get("YOUR_EMAIL", "")

TEMPLATE_PATH = ROOT / "outreach" / "templates" / "cold_email.html"
STATIC_DIR    = Path(__file__).parent / "static"

app = FastAPI(title="Berkeley Biz Dashboard")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ── helpers ──────────────────────────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    d = dict(row)
    for key in ("types", "photo_refs", "hours"):
        d[key] = json.loads(d.get(key) or "[]")
    return d


def _build_email_html(business: dict) -> tuple[str, str]:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = (
        template
        .replace("{{BUSINESS_NAME}}", business["name"])
        .replace("{{SITE_URL}}", business.get("site_url") or "#")
        .replace("{{YOUR_NAME}}", YOUR_NAME)
        .replace("{{YOUR_EMAIL}}", YOUR_EMAIL)
    )
    subject = f"I built a website for {business['name']}"
    return subject, html


def _generate_background(place_id: str) -> None:
    """Called in a thread — runs generate.py as a subprocess."""
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "generator" / "generate.py"), place_id],
            capture_output=True,
            text=True,
            timeout=600,
        )
        with DB._conn() as c:
            if result.returncode == 0:
                c.execute("UPDATE businesses SET generating = 0, generate_error = NULL WHERE place_id = ?", (place_id,))
            else:
                error = (result.stderr or result.stdout or "unknown error")[:500]
                c.execute("UPDATE businesses SET generating = 0, generate_error = ? WHERE place_id = ?", (error, place_id))
    except Exception as e:
        with DB._conn() as c:
            c.execute("UPDATE businesses SET generating = 0, generate_error = ? WHERE place_id = ?", (str(e), place_id))


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=FileResponse)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/stats")
def stats():
    with DB._conn() as c:
        def count(where=""):
            return c.execute(f"SELECT COUNT(*) FROM businesses {where}").fetchone()[0]
        return {
            "total":            count(),
            "no_site":          count("WHERE site_built=0 AND generating=0 AND skipped=0"),
            "generating":       count("WHERE generating=1"),
            "ready":            count("WHERE site_built=1 AND outreach_sent=0 AND skipped=0"),
            "sent":             count("WHERE outreach_sent=1"),
            "responded":        count("WHERE responded=1"),
            "sold":             count("WHERE sold=1"),
            "skipped":          count("WHERE skipped=1"),
        }


@app.get("/api/businesses")
def list_businesses(status: str = "all", search: str = ""):
    with DB._conn() as c:
        import sqlite3 as _sqlite3
        c.row_factory = _sqlite3.Row

        where, params = [], []
        if status == "no-site":
            where.append("site_built=0 AND generating=0 AND skipped=0")
        elif status == "generating":
            where.append("generating=1")
        elif status == "ready":
            where.append("site_built=1 AND outreach_sent=0 AND skipped=0")
        elif status == "sent":
            where.append("outreach_sent=1 AND responded=0 AND sold=0")
        elif status == "responded":
            where.append("responded=1")
        elif status == "sold":
            where.append("sold=1")
        elif status == "skipped":
            where.append("skipped=1")

        if search:
            where.append("(name LIKE ? OR address LIKE ?)")
            params += [f"%{search}%", f"%{search}%"]

        clause = ("WHERE " + " AND ".join(where)) if where else ""
        rows = c.execute(
            f"SELECT * FROM businesses {clause} ORDER BY rating DESC NULLS LAST LIMIT 200",
            params,
        ).fetchall()
        return [_row_to_dict(row) for row in rows]


@app.get("/api/businesses/{place_id}")
def get_business(place_id: str):
    b = DB.get_business(place_id)
    if not b:
        raise HTTPException(404, "Not found")
    return b


@app.get("/api/businesses/{place_id}/preview")
def preview_email(place_id: str):
    b = DB.get_business(place_id)
    if not b:
        raise HTTPException(404, "Not found")
    subject, html = _build_email_html(b)
    return {"subject": subject, "html": html}


class ApproveBody(BaseModel):
    email: str


@app.post("/api/businesses/{place_id}/approve")
def approve_and_send(place_id: str, body: ApproveBody):
    b = DB.get_business(place_id)
    if not b:
        raise HTTPException(404, "Not found")
    if not resend.api_key:
        raise HTTPException(400, "RESEND_API_KEY not set in .env")
    if not body.email:
        raise HTTPException(400, "Email address required")

    subject, html = _build_email_html(b)

    # Save email to DB
    with DB._conn() as c:
        c.execute("UPDATE businesses SET email = ? WHERE place_id = ?", (body.email, place_id))

    resp = resend.Emails.send({
        "from":    f"{YOUR_NAME} <{YOUR_EMAIL}>",
        "to":      [body.email],
        "subject": subject,
        "html":    html,
    })

    if resp.get("id"):
        DB.mark_outreach_sent(place_id)
        return {"ok": True, "resend_id": resp["id"]}
    else:
        raise HTTPException(500, f"Resend error: {resp}")


@app.post("/api/businesses/{place_id}/generate")
def trigger_generate(place_id: str):
    b = DB.get_business(place_id)
    if not b:
        raise HTTPException(404, "Not found")
    if b.get("generating"):
        return {"ok": True, "message": "already generating"}

    with DB._conn() as c:
        c.execute("UPDATE businesses SET generating=1, generate_error=NULL WHERE place_id=?", (place_id,))

    t = threading.Thread(target=_generate_background, args=(place_id,), daemon=True)
    t.start()
    return {"ok": True, "message": "generation started"}


@app.post("/api/businesses/{place_id}/skip")
def skip_business(place_id: str):
    with DB._conn() as c:
        c.execute("UPDATE businesses SET skipped=1 WHERE place_id=?", (place_id,))
    return {"ok": True}


@app.post("/api/businesses/{place_id}/unskip")
def unskip_business(place_id: str):
    with DB._conn() as c:
        c.execute("UPDATE businesses SET skipped=0 WHERE place_id=?", (place_id,))
    return {"ok": True}


class UpdateEmailBody(BaseModel):
    email: str


@app.put("/api/businesses/{place_id}/email")
def update_email(place_id: str, body: UpdateEmailBody):
    with DB._conn() as c:
        c.execute("UPDATE businesses SET email=? WHERE place_id=?", (body.email, place_id))
    return {"ok": True}


class MarkSoldBody(BaseModel):
    amount: float = 0


@app.post("/api/businesses/{place_id}/sold")
def mark_sold(place_id: str, body: MarkSoldBody):
    with DB._conn() as c:
        c.execute(
            "UPDATE businesses SET sold=1, sale_amount=? WHERE place_id=?",
            (body.amount, place_id),
        )
    return {"ok": True}


@app.post("/api/businesses/{place_id}/responded")
def mark_responded(place_id: str):
    with DB._conn() as c:
        c.execute("UPDATE businesses SET responded=1 WHERE place_id=?", (place_id,))
    return {"ok": True}

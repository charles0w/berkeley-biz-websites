"""Report this agent's run status to the CEO's Enterprise fleet dashboard.

POSTs to {CEOS_DASHBOARD_URL}/api/report with a shared-secret header.
Stdlib-only (urllib) — no extra deps. No-ops silently when CEOS_REPORT_SECRET
isn't set. Never raises — reporting must never crash a run.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone

AGENT_ID = "growth"
DEFAULT_URL = "https://ceos-enterprise.vercel.app"


def report(state: str, summary: str = "", ok: bool = True, **_kwargs) -> None:
    secret = os.environ.get("CEOS_REPORT_SECRET", "").strip()
    if not secret:
        return
    base = os.environ.get("CEOS_DASHBOARD_URL", DEFAULT_URL).strip().rstrip("/")
    payload = json.dumps({
        "agentId": AGENT_ID,
        "status": {
            "state": state,
            "lastRun": datetime.now(timezone.utc).isoformat(),
            "summary": summary[:280],
            "ok": ok,
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/api/report",
        data=payload,
        headers={"x-report-secret": secret, "content-type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:
        print(f"[ceo_report] post failed: {e}")

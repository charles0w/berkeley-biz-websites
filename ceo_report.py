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


def report(state: str, summary: str = "", ok: bool = True,
           metrics: list[dict] | None = None, progress: float | None = None,
           **_kwargs) -> None:
    """metrics: up to 3 {"label", "value", "unit"?, "money"?, "signed"?} card
    numbers; progress: 0..1 through the current task.

    Deliberately NO profit support here: growth's closed deals fund The
    Garage straight from the businesses table (closed_amount) — reporting
    profit too would double-count.
    """
    secret = os.environ.get("CEOS_REPORT_SECRET", "").strip()
    if not secret:
        return
    base = os.environ.get("CEOS_DASHBOARD_URL", DEFAULT_URL).strip().rstrip("/")
    status: dict = {
        "state": state,
        "lastRun": datetime.now(timezone.utc).isoformat(),
        "summary": summary[:280],
        "ok": ok,
    }
    if metrics:
        status["metrics"] = metrics[:3]
    if progress is not None:
        status["progress"] = max(0.0, min(1.0, float(progress)))
    payload = json.dumps({
        "agentId": AGENT_ID,
        "status": status,
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

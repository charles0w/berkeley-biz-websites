"""Report this agent's run status to the CEO's Enterprise fleet dashboard.

POSTs to {CEOS_DASHBOARD_URL}/api/report with a shared-secret header so the
`growth` card on ceos-enterprise reflects this repo's real autonomous runs
(scraping, site generation, outreach batches).

Stdlib-only (urllib) so it can be imported from any of the three pipeline
stages without pulling in `requests`. No-ops silently when CEOS_REPORT_SECRET
isn't set (local dev, CI without the secret), so it's safe to call
unconditionally. Never raises — status reporting must never crash a run.
"""
import json
import os
import urllib.request

AGENT_ID = "growth"
DEFAULT_URL = "https://ceos-enterprise.vercel.app"


def report(state: str, summary: str = "", ok: bool = True,
           *, cost_usd: float | None = None, duration_ms: int | None = None) -> None:
    secret = os.environ.get("CEOS_REPORT_SECRET", "").strip()
    if not secret:
        return  # not wired up — skip silently
    base = os.environ.get("CEOS_DASHBOARD_URL", DEFAULT_URL).strip().rstrip("/")
    payload = json.dumps({
        "agentId": AGENT_ID,
        "state": state,
        "summary": summary[:280],
        "ok": ok,
        "costUsd": cost_usd,
        "durationMs": duration_ms,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/api/report",
        data=payload,
        headers={"x-report-secret": secret, "content-type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:  # reporting must never crash the caller
        print(f"[ceo_report] post failed: {e}")

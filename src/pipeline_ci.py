"""
pipeline_ci.py — Africa Fuel Tracker · GitHub Actions Pipeline
==============================================================
Step 1 : Fetch live FX rates
Step 2 : Build records from real_prices.json (42 countries verified)
         + Try Playwright for any new weekly prices
Step 3 : Generate Excel workbook  → docs/africa_fuel_prices.xlsx
Step 4 : Generate HTML dashboard  → docs/index.html
"""

import sys, os, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC  = Path(__file__).parent
DOCS = ROOT / "docs"; DOCS.mkdir(exist_ok=True)
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)

EXCEL_OUT = DOCS / "africa_fuel_prices.xlsx"
HTML_OUT  = DOCS / "index.html"
LOG_OUT   = DOCS / "last_update.txt"

sys.path.insert(0, str(SRC))


def log(msg):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}]  {msg}", flush=True)


def run():
    log("=" * 62)
    log("  🚀  AFRICA FUEL TRACKER — GITHUB ACTIONS PIPELINE")
    log("=" * 62)

    import data as D
    import excel_builder as EB
    import dashboard_builder as DB

    # ── 1. Fetch live FX rates ──────────────────────────────────────────────
    log("STEP 1/4 — Fetching live FX rates …")
    fx = D.fetch_live_fx()
    log(f"   → {len(fx)} currencies ready")

    # ── 2. Build records from real data ────────────────────────────────────
    log("STEP 2/4 — Building records from verified real data …")
    log("   → Primary  : real_prices.json (42 countries, A/B/C/D sources)")
    log("   → Fallback  : seed estimates  (12 countries, no confirmed source)")

    # Optionally try Playwright for new weekly updates
    try:
        from collector import run_collection, build_records_from_db
        log("   → Attempting live collection via Playwright …")
        run_collection()
        records = build_records_from_db(fx)
        live_n = sum(1 for r in records if r.get("data_quality") == "live")
        if live_n > 0:
            log(f"   → {live_n} countries updated with live Playwright data")
        else:
            log("   → Playwright yielded no new data — using real_prices.json")
            records = D.build_records(fx)
    except Exception as e:
        log(f"   → Collector unavailable ({e}) — using real_prices.json")
        records = D.build_records(fx)

    real_n = sum(1 for r in records if r.get("data_quality") in ("real", "live"))
    est_n  = sum(1 for r in records if r.get("data_quality") == "estimated")
    log(f"   → {len(records)} countries | {real_n} real/verified | {est_n} estimated")

    # ── 3. Build JSON payload ───────────────────────────────────────────────
    payload = D.build_json_payload(records, fx)

    # ── 4. Generate Excel ───────────────────────────────────────────────────
    log("STEP 3/4 — Generating Excel workbook …")
    EB.build(records, fx, D.CB_SOURCES, D.WEEK_LABELS, str(EXCEL_OUT))

    # ── 5. Generate Dashboard ───────────────────────────────────────────────
    log("STEP 4/4 — Generating HTML dashboard …")
    DB.build(payload, str(HTML_OUT))

    # ── 6. Write status log ─────────────────────────────────────────────────
    now = datetime.datetime.utcnow()
    LOG_OUT.write_text(
        f"Last updated : {now.strftime('%d %B %Y — %H:%M UTC')}\n"
        f"Countries    : {len(records)}\n"
        f"Real verified: {real_n} (sources A=GPP, B=RhinoCarHire, C=Press, D=Official)\n"
        f"Estimated    : {est_n} (12 countries, no confirmed source available)\n"
        f"Period       : 05 Jan 2026 — 21 Mar 2026 (12 weekly snapshots)\n"
        f"FX currencies: {len(fx)}\n"
        f"Sources      : GlobalPetrolPrices.com · RhinoCarHire.com · Zawya · Vanguard · gov.za · EPRA · NNPC · EGP\n"
    )

    log("=" * 62)
    log("  ✅  PIPELINE COMPLETE")
    log(f"      Excel    : docs/africa_fuel_prices.xlsx")
    log(f"      Dashboard: docs/index.html")
    log("=" * 62)


if __name__ == "__main__":
    run()

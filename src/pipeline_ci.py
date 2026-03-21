"""
pipeline_ci.py — Africa Fuel Tracker · GitHub Actions Pipeline
==============================================================
Step 1 : Fetch live FX rates
Step 2 : Collect REAL prices from GlobalPetrolPrices.com + national authorities
Step 3 : Generate Excel workbook  → docs/africa_fuel_prices.xlsx
Step 4 : Generate HTML dashboard  → docs/index.html
"""

import sys, os, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC  = Path(__file__).parent
DOCS = ROOT / "data"; DOCS.mkdir(exist_ok=True)   # prices_db.json goes here
DOCS = ROOT / "docs"; DOCS.mkdir(exist_ok=True)   # served by GitHub Pages

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
    import collector as C

    # ── 1. Fetch live FX rates ──────────────────────────────────────────────
    log("STEP 1/4 — Fetching live FX rates …")
    fx = D.fetch_live_fx()
    log(f"   → {len(fx)} currencies ready")

    # ── 2. Collect real prices ──────────────────────────────────────────────
    log("STEP 2/4 — Collecting real prices from official sources …")
    log("   → Primary  : GlobalPetrolPrices.com (weekly pump prices)")
    log("   → Secondary: National energy regulatory portals")
    log("   → Tertiary : World Bank commodity benchmarks")

    try:
        C.run_collection()
        records = C.build_records_from_db(fx)
        live_count = sum(1 for r in records if r.get("data_quality") == "live")
        log(f"   → {len(records)} countries · {live_count} with live data")
    except Exception as e:
        log(f"   ⚠️  Collector error: {e} — falling back to seed data")
        records = D.build_records(fx)

    # ── 3. Build JSON payload ───────────────────────────────────────────────
    payload = D.build_json_payload(records, fx)
    # Add data quality info to payload
    payload["data_quality_summary"] = {
        "live":    sum(1 for r in records if r.get("data_quality") == "live"),
        "partial": sum(1 for r in records if r.get("data_quality") == "partial"),
        "seed":    sum(1 for r in records if r.get("data_quality") == "seed"),
        "total":   len(records),
    }

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
        f"Live data    : {payload['data_quality_summary']['live']}\n"
        f"Partial data : {payload['data_quality_summary']['partial']}\n"
        f"Seed fallback: {payload['data_quality_summary']['seed']}\n"
        f"FX currencies: {len(fx)}\n"
        f"Sources      : GlobalPetrolPrices.com · National Regulatory Portals · World Bank\n"
    )

    log("=" * 62)
    log("  ✅  PIPELINE COMPLETE")
    log(f"      Excel   : docs/africa_fuel_prices.xlsx")
    log(f"      Dashboard: docs/index.html")
    log(f"      DB      : data/prices_db.json")
    log("=" * 62)


if __name__ == "__main__":
    run()

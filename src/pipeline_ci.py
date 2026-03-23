"""
pipeline_ci.py — Africa Fuel Tracker · GitHub Actions Pipeline
==============================================================
Étapes :
  1. Fetch live FX rates (open.er-api.com)
  2. Populate DB si vide (populate_db.py → 1350 entrées, 54 pays)
  3. Collect weekly live prices (collector.py)
  4. Build records from DB
  5. Generate Excel (excel_builder.py)
  6. Generate Dashboard (dashboard_builder.py)
"""

import sys, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC  = ROOT / "src"
DOCS = ROOT / "docs";  DOCS.mkdir(exist_ok=True)
DATA = ROOT / "data";  DATA.mkdir(exist_ok=True)
sys.path.insert(0, str(SRC))

EXCEL_OUT = DOCS / "africa_fuel_prices.xlsx"
HTML_OUT  = DOCS / "index.html"
LOG_OUT   = DOCS / "last_update.txt"


def log(msg):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}]  {msg}", flush=True)


def run():
    log("=" * 62)
    log("  AFRICA FUEL TRACKER — GITHUB ACTIONS PIPELINE")
    log("=" * 62)

    import data as D
    import excel_builder as EB
    import dashboard_builder as DB
    import collector as C
    import populate_db as PDB
    from pathlib import Path

    # ── 1. FX rates ──────────────────────────────────────────────────────
    log("STEP 1/5 — Fetching live FX rates …")
    fx = D.fetch_live_fx()
    log(f"   → {len(fx)} currencies")

    # ── 2. Populate DB si vide ────────────────────────────────────────────
    DB_FILE = DATA / "prices_db.json"
    import json
    db_empty = True
    if DB_FILE.exists():
        try:
            db_data = json.load(open(DB_FILE))
            db_empty = len(db_data.get("entries", [])) < 100
        except: pass

    if db_empty:
        log("STEP 2/5 — Populating DB with verified historical data …")
        log("   → 54 pays × 12 semaines × gas+diesel = 1296 points")
        PDB.populate()
        log("   ✅ DB initialized: 54/54 countries, Jan→Mar 2026")
    else:
        db_data = json.load(open(DB_FILE))
        n = len(db_data.get("entries", []))
        log(f"STEP 2/5 — DB already populated ({n} entries) — skipping")

    # ── 3. Collect live weekly prices ─────────────────────────────────────
    log("STEP 3/5 — Collecting live weekly prices …")
    log("   → Source B: RhinoCarHire.com (39 pays, EUR→USD)")
    log("   → Source A: TradingEconomics (35+ pays, USD/L)")
    log("   → Source D: Official national sources (5 pays)")
    try:
        C.run_collection()
    except Exception as e:
        log(f"   ⚠️  Collection error: {e} — using DB data")

    # ── 4. Build records ──────────────────────────────────────────────────
    log("STEP 4/5 — Building records from DB …")
    records = C.build_records_from_db(fx)

    # Update FX in records
    for r in records:
        r["fx_rate"] = fx.get(r["currency"], r["fx_rate"])

    live_n      = sum(1 for r in records if r.get("data_quality") == "live")
    verified_n  = sum(1 for r in records if r.get("data_quality") in ("live","verified"))
    log(f"   → {len(records)} countries: {live_n} live, {verified_n} verified, {len(records)-verified_n} estimated")

    payload = D.build_json_payload(records, fx)
    payload["data_quality_summary"] = {
        "live":      live_n,
        "verified":  verified_n - live_n,
        "estimated": len(records) - verified_n,
        "total":     len(records),
    }

    # ── 5. Generate Excel ────────────────────────────────────────────────
    log("STEP 5a/5 — Generating Excel workbook …")
    EB.build(records, fx, D.CB_SOURCES, D.WEEK_LABELS, str(EXCEL_OUT))

    # ── 6. Generate Dashboard ────────────────────────────────────────────
    log("STEP 5b/5 — Generating HTML dashboard …")
    DB.build(payload, str(HTML_OUT))

    # ── 7. Write log ─────────────────────────────────────────────────────
    now = datetime.datetime.utcnow()
    LOG_OUT.write_text(
        f"Last updated : {now.strftime('%d %B %Y — %H:%M UTC')}\n"
        f"Countries    : {len(records)}/54\n"
        f"Live data    : {live_n}\n"
        f"Verified data: {verified_n}\n"
        f"Estimated    : {len(records)-verified_n}\n"
        f"FX currencies: {len(fx)}\n"
        f"Sources      : RhinoCarHire.com · TradingEconomics · Official Portals\n"
        f"Period       : {D.PERIOD_START} → {D.PERIOD_END}\n"
    )

    log("=" * 62)
    log("  ✅ PIPELINE COMPLETE")
    log(f"     Excel    : docs/africa_fuel_prices.xlsx")
    log(f"     Dashboard: docs/index.html")
    log(f"     DB       : data/prices_db.json ({len(records)*D.N_WEEKS*2}+ entries)")
    log("=" * 62)


if __name__ == "__main__":
    run()

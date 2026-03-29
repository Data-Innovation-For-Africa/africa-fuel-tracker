"""
run_all_scrapers.py — Africa Fuel Tracker Orchestrator

Runs all 54 country scrapers sequentially.
On success  → updates prices_db.json + appends to history_db.json
On failure  → keeps last known value, marks status='stale'
After all   → writes final prices_db.json with updated meta
"""
import importlib
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.base import CountryResult, ScraperError, validate_price
from utils.fx import get_rate, local_to_usd
from utils.db import (
    load_prices, save_prices, append_history,
    build_history_record, compute_deltas, get_last_known
)

# ── Country → scraper module mapping (alphabetical by module name) ───────────
SCRAPERS = [
    # North Africa
    ("Algeria",          "scrapers.dz_algeria"),
    ("Egypt",            "scrapers.eg_egypt"),
    ("Libya",            "scrapers.ly_libya"),
    ("Morocco",          "scrapers.ma_morocco"),
    ("Sudan",            "scrapers.sd_sudan"),
    ("Tunisia",          "scrapers.tn_tunisia"),
    # West Africa
    ("Benin",            "scrapers.bj_benin"),
    ("Burkina Faso",     "scrapers.bf_burkina_faso"),
    ("Cabo Verde",       "scrapers.cv_cabo_verde"),
    ("Gambia",           "scrapers.gm_gambia"),
    ("Ghana",            "scrapers.gh_ghana"),
    ("Guinea",           "scrapers.gn_guinea"),
    ("Guinea-Bissau",    "scrapers.gw_guinea_bissau"),
    ("Ivory Coast",      "scrapers.ci_ivory_coast"),
    ("Liberia",          "scrapers.lr_liberia"),
    ("Mali",             "scrapers.ml_mali"),
    ("Mauritania",       "scrapers.mr_mauritania"),
    ("Niger",            "scrapers.ne_niger"),
    ("Nigeria",          "scrapers.ng_nigeria"),
    ("Senegal",          "scrapers.sn_senegal"),
    ("Sierra Leone",     "scrapers.sl_sierra_leone"),
    ("Togo",             "scrapers.tg_togo"),
    # Central Africa
    ("CAR",              "scrapers.cf_car"),
    ("Cameroon",         "scrapers.cm_cameroon"),
    ("Chad",             "scrapers.td_chad"),
    ("Congo DR",         "scrapers.cd_congo_dr"),
    ("Congo Republic",   "scrapers.cg_congo_republic"),
    ("Equatorial Guinea","scrapers.gq_equatorial_guinea"),
    ("Gabon",            "scrapers.ga_gabon"),
    ("Sao Tome",         "scrapers.st_sao_tome"),
    # East Africa
    ("Burundi",          "scrapers.bi_burundi"),
    ("Comoros",          "scrapers.km_comoros"),
    ("Djibouti",         "scrapers.dj_djibouti"),
    ("Eritrea",          "scrapers.er_eritrea"),
    ("Ethiopia",         "scrapers.et_ethiopia"),
    ("Kenya",            "scrapers.ke_kenya"),
    ("Madagascar",       "scrapers.mg_madagascar"),
    ("Malawi",           "scrapers.mw_malawi"),
    ("Mauritius",        "scrapers.mu_mauritius"),
    ("Rwanda",           "scrapers.rw_rwanda"),
    ("Seychelles",       "scrapers.sc_seychelles"),
    ("Somalia",          "scrapers.so_somalia"),
    ("South Sudan",      "scrapers.ss_south_sudan"),
    ("Tanzania",         "scrapers.tz_tanzania"),
    ("Uganda",           "scrapers.ug_uganda"),
    # Southern Africa
    ("Angola",           "scrapers.ao_angola"),
    ("Botswana",         "scrapers.bw_botswana"),
    ("Eswatini",         "scrapers.sz_eswatini"),
    ("Lesotho",          "scrapers.ls_lesotho"),
    ("Mozambique",       "scrapers.mz_mozambique"),
    ("Namibia",          "scrapers.na_namibia"),
    ("South Africa",     "scrapers.za_south_africa"),
    ("Zambia",           "scrapers.zm_zambia"),
    ("Zimbabwe",         "scrapers.zw_zimbabwe"),
]


def run_scraper(country: str, module_path: str, existing_data: dict) -> tuple[dict, str]:
    """
    Run one country scraper.
    Returns (record_dict, status) where status is 'ok' | 'stale' | 'error'.
    """
    try:
        mod = importlib.import_module(module_path)
        result: CountryResult = mod.scrape()

        # Validate price range
        if not validate_price(result.iso2, result.gas_loc, result.die_loc):
            raise ScraperError(
                f"Price out of expected range: gas={result.gas_loc}, die={result.die_loc}"
            )

        # Get FX rate
        fx_info = get_rate(result.currency)
        fx_rate = fx_info.get("rate")

        if fx_rate is None or fx_rate <= 0:
            raise ScraperError(f"No FX rate available for {result.currency}")

        result.fx_rate   = fx_rate
        result.fx_source = fx_info.get("source", "unknown")
        result.fx_date   = fx_info.get("date", "")
        result.gas_usd   = round(result.gas_loc / fx_rate, 4)
        result.die_usd   = round(result.die_loc / fx_rate, 4)
        result.scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result.status    = "ok"

        # Compute deltas vs last known value
        delta_gas, delta_die = compute_deltas(country, result.gas_usd, result.die_usd)
        result.delta_gas_usd = delta_gas
        result.delta_die_usd = delta_die

        record = result.to_dict()
        print(f"  ✅ {country:<22} gas={result.gas_loc} {result.currency} "
              f"(${result.gas_usd:.3f}) | die={result.die_loc} (${result.die_usd:.3f})")
        return record, "ok"

    except Exception as e:
        # ── Failure → keep last known value ──────────────────────────────────
        last = existing_data.get(country)
        if last:
            last["status"]     = "stale"
            last["scraped_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            last["delta_gas_usd"] = 0.0
            last["delta_die_usd"] = 0.0
            err_type = type(e).__name__
            print(f"  ⚠️  {country:<22} STALE ({err_type}: {str(e)[:60]})")
            return last, "stale"
        else:
            print(f"  ❌ {country:<22} ERROR — no previous data available: {e}")
            return {}, "error"


def main():
    print(f"\n{'='*60}")
    print(f"Africa Fuel Tracker — Daily Update")
    print(f"Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    existing = load_prices()
    existing_data = existing.get("data", {})

    new_data = {}
    counts = {"ok": 0, "stale": 0, "error": 0}

    for country, module_path in SCRAPERS:
        record, status = run_scraper(country, module_path, existing_data)
        if record:
            new_data[country] = record
            counts[status] += 1

            # Append to history only if ok or stale (not empty error)
            if status in ("ok", "stale"):
                hist_record = build_history_record(record)
                append_history(country, hist_record)

    # Write final prices_db.json
    meta = {
        "last_updated":     datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_date":         datetime.now(timezone.utc).date().isoformat(),
        "countries_total":  len(SCRAPERS),
        "countries_ok":     counts["ok"],
        "countries_stale":  counts["stale"],
        "countries_error":  counts["error"],
    }
    save_prices(new_data, meta)

    print(f"\n{'='*60}")
    print(f"Done — ✅ {counts['ok']} ok | ⚠️  {counts['stale']} stale | ❌ {counts['error']} error")
    print(f"prices_db.json updated ({len(new_data)} countries)")
    print(f"{'='*60}\n")

    # Exit with error code if too many failures (> 10 countries stale/error)
    if counts["stale"] + counts["error"] > 10:
        print("⚠️  WARNING: more than 10 countries failed. Check scraper logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
JSON database utilities for prices_db.json and history_db.json.
Thread-safe writes via atomic rename pattern.
"""
import json
import os
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

DATA_DIR     = Path(__file__).parent.parent / "data"
PRICES_DB    = DATA_DIR / "prices_db.json"
HISTORY_DB   = DATA_DIR / "history_db.json"


# ── Read ──────────────────────────────────────────────────────────────────────

def load_prices() -> dict:
    """Load current prices_db.json. Returns empty structure if file missing."""
    if not PRICES_DB.exists():
        return {"meta": {}, "data": {}}
    with open(PRICES_DB, encoding="utf-8") as f:
        return json.load(f)


def load_history() -> dict:
    """Load history_db.json. Returns {} if file missing."""
    if not HISTORY_DB.exists():
        return {}
    with open(HISTORY_DB, encoding="utf-8") as f:
        return json.load(f)


def get_last_known(country: str) -> dict | None:
    """Return last known record for a country from prices_db (used on scrape failure)."""
    db = load_prices()
    return db["data"].get(country)


# ── Write ─────────────────────────────────────────────────────────────────────

def _atomic_write(path: Path, data: dict) -> None:
    """Write JSON atomically via temp file + rename."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def save_prices(data: dict, meta: dict) -> None:
    """Overwrite prices_db.json with updated meta + data."""
    _atomic_write(PRICES_DB, {"meta": meta, "data": data})


def append_history(country: str, record: dict) -> None:
    """
    Append one record to country's history.
    If today's date already exists, overwrite it (idempotent re-runs).
    """
    history = load_history()
    entries = history.get(country, [])
    today   = date.today().isoformat()

    # Remove existing entry for today (so re-runs don't duplicate)
    entries = [e for e in entries if e.get("date") != today]
    entries.append(record)

    # Keep max 3 years of daily data (~1100 entries) per country
    entries = entries[-1100:]

    history[country] = entries
    _atomic_write(HISTORY_DB, history)


def build_history_record(country_data: dict) -> dict:
    """Extract a minimal history record from a full country data dict."""
    return {
        "date":     date.today().isoformat(),
        "gas_loc":  country_data.get("gas_loc"),
        "die_loc":  country_data.get("die_loc"),
        "gas_usd":  country_data.get("gas_usd"),
        "die_usd":  country_data.get("die_usd"),
        "fx_rate":  country_data.get("fx_rate"),
        "status":   country_data.get("status"),
        "source_url": country_data.get("source_url"),
    }


# ── Delta calculation ─────────────────────────────────────────────────────────

def compute_deltas(country: str, new_gas_usd: float, new_die_usd: float) -> tuple[float, float]:
    """
    Return (delta_gas_usd, delta_die_usd) vs yesterday's values.
    Returns (0.0, 0.0) if no history available.
    """
    history = load_history()
    entries = history.get(country, [])
    today   = date.today().isoformat()
    prev    = [e for e in entries if e.get("date") != today and e.get("status") == "ok"]
    if not prev:
        return 0.0, 0.0
    last = prev[-1]
    delta_gas = round(new_gas_usd - (last.get("gas_usd") or 0), 4)
    delta_die = round(new_die_usd - (last.get("die_usd") or 0), 4)
    return delta_gas, delta_die

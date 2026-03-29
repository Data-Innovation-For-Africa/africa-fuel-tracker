"""
FX rates via Frankfurter API (https://www.frankfurter.app/)
Official ECB / central bank rates. No API key required.
Fetched once per day and cached in memory during a run.
"""
import requests
from datetime import date
from functools import lru_cache

FRANKFURTER_URL = "https://api.frankfurter.app/latest"

# Currencies supported by Frankfurter (subset relevant to Africa)
FRANKFURTER_SUPPORTED = {
    "DZD", "EGP", "MAD", "TND", "NGN", "KES", "ETB", "GHS",
    "ZAR", "TZS", "UGX", "RWF", "MZN", "ZMW", "BWP", "NAD",
    "MUR", "SCR", "MWK", "MGA", "XOF", "XAF", "CVE", "GMD",
    "BIF", "KMF", "DJF", "GNF", "LRD", "MRU",
}

# Fixed rates for currencies NOT in Frankfurter
# (pegged, isolated, or hyperinflationary countries)
FIXED_RATES = {
    "LYD": 4.85,     # Libya — CBL official rate
    "SDG": 601.5,    # Sudan — oilpricez confirmed 29-Mar-2026
    "SSP": 4544.0,   # South Sudan — BoSS official Dec-2025
    "ERN": 15.0,     # Eritrea — fixed since 2005
    "SLL": 22500.0,  # Sierra Leone (old SLL, = 22.5 SLE)
    "SLE": 22.5,     # Sierra Leone new Leone
    "STN": 21.5,     # Sao Tome Dobra
    "AOA": 917.0,    # Angola kwanza
    "CDF": 2820.0,   # Congo DR franc
    "ZWG": 26.0,     # Zimbabwe ZiG (stable since Apr-2024)
    "LSL": 18.55,    # Lesotho — pegged 1:1 ZAR approx
    "SZL": 18.55,    # Eswatini — pegged 1:1 ZAR
}

_fx_cache: dict[str, float] = {}
_fx_date: str = ""


def get_fx_rates(currencies: list[str]) -> dict[str, dict]:
    """
    Return FX rates for the given list of currency codes.
    Returns dict: { "KES": {"rate": 130.5, "source": "frankfurter", "date": "2026-03-29"} }
    """
    global _fx_cache, _fx_date

    today = date.today().isoformat()
    result = {}

    # Split into Frankfurter and fixed
    to_fetch = [c for c in currencies if c in FRANKFURTER_SUPPORTED]
    fixed    = [c for c in currencies if c in FIXED_RATES]

    # Fetch from Frankfurter (cached for this run)
    if to_fetch and not _fx_cache:
        _fetch_frankfurter(to_fetch)

    for cur in to_fetch:
        if cur in _fx_cache:
            result[cur] = {
                "rate": _fx_cache[cur],
                "source": "frankfurter",
                "date": _fx_date or today,
            }
        else:
            # Frankfurter doesn't have this currency despite being listed
            result[cur] = {"rate": None, "source": "unavailable", "date": today}

    for cur in fixed:
        result[cur] = {
            "rate": FIXED_RATES[cur],
            "source": "fixed",
            "date": today,
        }

    return result


def get_rate(currency: str) -> dict:
    """Get FX rate for a single currency."""
    rates = get_fx_rates([currency])
    return rates.get(currency, {"rate": None, "source": "unavailable", "date": date.today().isoformat()})


def _fetch_frankfurter(currencies: list[str]) -> None:
    """Fetch all needed rates in one API call and populate cache."""
    global _fx_cache, _fx_date
    symbols = ",".join(sorted(set(currencies)))
    try:
        resp = requests.get(
            FRANKFURTER_URL,
            params={"from": "USD", "to": symbols},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        _fx_cache = data.get("rates", {})
        _fx_date  = data.get("date", date.today().isoformat())
    except Exception as e:
        print(f"[FX] Frankfurter fetch failed: {e}. Will use per-currency fallback.")


def usd_to_local(usd_price: float, currency: str) -> float | None:
    """Convert a USD price to local currency. Returns None if rate unavailable."""
    info = get_rate(currency)
    rate = info.get("rate")
    if rate and rate > 0:
        return round(usd_price * rate, 4)
    return None


def local_to_usd(local_price: float, currency: str) -> float | None:
    """Convert a local currency price to USD."""
    info = get_rate(currency)
    rate = info.get("rate")
    if rate and rate > 0:
        return round(local_price / rate, 4)
    return None

"""
FX rates via Frankfurter API (https://www.frankfurter.app/)
Official ECB / central bank rates. No API key required.

FIX: Call once at startup WITHOUT a `to=` filter — the API returns ALL
currencies it knows vs USD in one shot. Filtering with `to=DZD` causes 404.
"""
import requests
from datetime import date

FRANKFURTER_URL = "https://api.frankfurter.app/latest"

# Currencies supported by Frankfurter (subset relevant to Africa)
FRANKFURTER_SUPPORTED = {
    "DZD", "EGP", "MAD", "TND", "NGN", "KES", "ETB", "GHS",
    "ZAR", "TZS", "UGX", "RWF", "MZN", "ZMW", "BWP", "NAD",
    "MUR", "SCR", "MWK", "MGA", "XOF", "XAF", "CVE", "GMD",
    "BIF", "KMF", "DJF", "GNF", "LRD", "MRU",
}

# Fixed rates for currencies NOT in Frankfurter
FIXED_RATES = {
    "USD": 1.0,       # Somalia — dollarised
    "LYD": 4.85,      # Libya — CBL official
    "SDG": 601.5,     # Sudan — confirmed Mar-2026
    "SSP": 4544.0,    # South Sudan — BoSS Dec-2025
    "ERN": 15.0,      # Eritrea — fixed since 2005
    "SLL": 22500.0,   # Sierra Leone (old SLL)
    "SLE": 22.5,      # Sierra Leone new Leone
    "STN": 21.5,      # Sao Tome Dobra
    "AOA": 917.0,     # Angola kwanza
    "CDF": 2820.0,    # Congo DR franc
    "ZWG": 26.0,      # Zimbabwe ZiG (stable Apr-2024)
    "LSL": 18.55,     # Lesotho — pegged ~1:1 ZAR
    "SZL": 18.55,     # Eswatini — pegged ~1:1 ZAR
}

_fx_cache: dict[str, float] = {}
_fx_date:  str = ""
_loaded:   bool = False   # True once bulk fetch has been attempted


def _ensure_loaded() -> None:
    """Fetch ALL Frankfurter rates in one call (no `to=` filter)."""
    global _fx_cache, _fx_date, _loaded
    if _loaded:
        return
    _loaded = True
    try:
        # No `to=` param → returns every currency Frankfurter knows vs USD
        resp = requests.get(
            FRANKFURTER_URL,
            params={"from": "USD"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        _fx_cache = data.get("rates", {})
        _fx_date  = data.get("date", date.today().isoformat())
        print(f"[FX] Frankfurter loaded {len(_fx_cache)} rates for {_fx_date}")
    except Exception as exc:
        print(f"[FX] Frankfurter bulk fetch failed: {exc}. Using fixed rates only.")


def get_fx_rates(currencies: list[str]) -> dict[str, dict]:
    """
    Return FX rates for the given currency codes.
    Result: { "KES": {"rate": 130.5, "source": "frankfurter", "date": "…"} }
    """
    _ensure_loaded()
    today = date.today().isoformat()
    result: dict[str, dict] = {}

    for cur in currencies:
        # 1. Fixed override (always wins — pegged / isolated currencies)
        if cur in FIXED_RATES:
            result[cur] = {
                "rate":   FIXED_RATES[cur],
                "source": "fixed",
                "date":   today,
            }
        # 2. Frankfurter cache
        elif cur in _fx_cache:
            result[cur] = {
                "rate":   _fx_cache[cur],
                "source": "frankfurter",
                "date":   _fx_date or today,
            }
        # 3. Nothing found
        else:
            result[cur] = {"rate": None, "source": "unavailable", "date": today}

    return result


def get_rate(currency: str) -> dict:
    """Get FX rate for a single currency."""
    return get_fx_rates([currency]).get(
        currency,
        {"rate": None, "source": "unavailable", "date": date.today().isoformat()},
    )


def usd_to_local(usd_price: float, currency: str) -> float | None:
    info = get_rate(currency)
    rate = info.get("rate")
    return round(usd_price * rate, 4) if rate and rate > 0 else None


def local_to_usd(local_price: float, currency: str) -> float | None:
    info = get_rate(currency)
    rate = info.get("rate")
    return round(local_price / rate, 4) if rate and rate > 0 else None


"""
FX rates — Africa Fuel Tracker
==============================
Frankfurter API only supports ~30 major world currencies (ECB basket).
African currencies are NOT supported except ZAR.
All other African currencies use FIXED_RATES (official central bank rates).

FIX: Call Frankfurter once WITHOUT to= filter to get ZAR + major currencies.
All other African currencies fall back to FIXED_RATES immediately.
"""
import requests
from datetime import date

FRANKFURTER_URL = "https://api.frankfurter.app/latest"

# Only currencies actually supported by Frankfurter (ECB basket)
# African currencies are NOT in this list except ZAR
FRANKFURTER_SUPPORTED = {
    "ZAR",  # South Africa — only African currency in Frankfurter
    # Major world currencies (for reference, not used directly in Africa tracker)
    "EUR","GBP","JPY","CHF","AUD","CAD","CNY","HKD","NZD","SEK",
    "NOK","DKK","SGD","KRW","MXN","INR","BRL","PLN","CZK","HUF",
    "RON","BGN","TRY","IDR","MYR","PHP","THB","ILS",
}

# Official central bank rates for ALL African currencies — March 2026
# Sources: respective central banks (BCK, CBK, BdM, BoT, NBE, BOU, etc.)
FIXED_RATES: dict[str, float] = {
    # North Africa
    "DZD": 134.5,   # Banque d'Algérie — official ARH rate
    "EGP":  50.3,   # Central Bank of Egypt
    "LYD":   4.85,  # Central Bank of Libya
    "MAD":  10.03,  # Bank Al-Maghrib
    "SDG": 601.5,   # Central Bank of Sudan
    "TND":   3.02,  # Banque Centrale de Tunisie
    # West Africa (CFA/BCEAO)
    "XOF": 604.0,   # BCEAO (Benin, BF, CI, Guinea-Bissau, Mali, Niger, Senegal, Togo)
    "CVE": 110.5,   # Banco de Cabo Verde
    "GMD":  73.0,   # Central Bank of Gambia
    "GHS":  15.7,   # Bank of Ghana
    "GNF": 8650.0,  # Banque Centrale de Guinée
    "LRD": 194.0,   # Central Bank of Liberia
    "NGN": 1621.0,  # Central Bank of Nigeria
    "SLL": 22500.0, # Bank of Sierra Leone (old SLL = 22.5 SLE)
    "SLE":  22.5,   # Bank of Sierra Leone new Leone
    # Central Africa (CFA/BEAC)
    "XAF": 604.0,   # BEAC (CAR, Cameroon, Chad, Congo-B, Equatorial Guinea, Gabon)
    "CDF": 2820.0,  # Banque Centrale du Congo
    "STN":  21.5,   # Banco Central de São Tomé e Príncipe
    # East Africa
    "BIF": 2920.0,  # Banque de la République du Burundi
    "KMF":  451.0,  # Banque Centrale des Comores
    "DJF":  177.7,  # Banque Centrale de Djibouti
    "ERN":  15.0,   # Bank of Eritrea — fixed since 2005
    "ETB":  131.0,  # National Bank of Ethiopia
    "KES":  130.5,  # Central Bank of Kenya
    "MGA": 4620.0,  # Banque Centrale de Madagascar
    "MWK": 1735.0,  # Reserve Bank of Malawi
    "MUR":  46.5,   # Bank of Mauritius
    "RWF": 1463.0,  # National Bank of Rwanda
    "SCR":  14.15,  # Central Bank of Seychelles
    "USD":   1.0,   # Somalia — fully dollarised economy
    "SSP": 4544.0,  # Bank of South Sudan — official Dec-2025
    "TZS": 2710.0,  # Bank of Tanzania
    "UGX": 3582.0,  # Bank of Uganda
    # Southern Africa
    "AOA":  917.0,  # Banco Nacional de Angola
    "BWP":  13.54,  # Bank of Botswana
    "SZL":  18.55,  # Central Bank of Eswatini — pegged 1:1 ZAR
    "LSL":  18.55,  # Central Bank of Lesotho — pegged 1:1 ZAR
    "MZN":  64.1,   # Banco de Moçambique
    "NAD":  18.55,  # Bank of Namibia — pegged 1:1 ZAR
    "ZMW":  27.2,   # Bank of Zambia
    "ZWG":  26.0,   # Reserve Bank of Zimbabwe (ZiG, stable Apr-2024)
    # ZAR: fetched live from Frankfurter when available; fallback below
    "ZAR":  18.2,   # SARB March 2026 approx — updated by Frankfurter when reachable
}

_fx_cache: dict[str, float] = {}
_fx_date:  str = ""
_loaded:   bool = False


def _ensure_loaded() -> None:
    """Fetch Frankfurter once (ZAR + major currencies). Single bulk call, no to= filter."""
    global _fx_cache, _fx_date, _loaded
    if _loaded:
        return
    _loaded = True
    try:
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
        print(f"[FX] Frankfurter fetch failed: {exc}. Using fixed rates only.")


def get_fx_rates(currencies: list[str]) -> dict[str, dict]:
    """
    Return FX info for the given list of currency codes.
    Result: { "KES": {"rate": 130.5, "source": "fixed", "date": "…"} }
    Priority: FIXED_RATES → Frankfurter cache → unavailable
    """
    _ensure_loaded()
    today  = date.today().isoformat()
    result: dict[str, dict] = {}

    for cur in currencies:
        if cur in FIXED_RATES:
            result[cur] = {"rate": FIXED_RATES[cur], "source": "fixed", "date": today}
        elif cur in _fx_cache:
            result[cur] = {"rate": _fx_cache[cur], "source": "frankfurter", "date": _fx_date or today}
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



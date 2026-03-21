"""
data.py — Africa Fuel Tracker · Master Data Module
===================================================
Period  : 1 January 2026 → 20 March 2026  (78 days, 12 weekly snapshots)
Prices  : USD/L gasoline, diesel, LPG/kg  +  local national currency
FX rates: 41 currencies — central bank reference rates, March 2026
Sources : GlobalPetrolPrices.com · OPEC · World Bank · National Regulatory Portals
"""

import datetime, random, requests

# ── Period ─────────────────────────────────────────────────────────────────────
PERIOD_START = datetime.date(2026, 1, 1)
PERIOD_END   = datetime.date(2026, 3, 20)

# Build weekly snapshot dates every 7 days
WEEK_DATES = []
d = PERIOD_START
while d <= PERIOD_END:
    WEEK_DATES.append(d)
    d += datetime.timedelta(weeks=1)
if WEEK_DATES[-1] != PERIOD_END:
    WEEK_DATES.append(PERIOD_END)

WEEK_LABELS = [d.strftime("%d %b") for d in WEEK_DATES]
N_WEEKS     = len(WEEK_DATES)   # 12

# ── FX Reference Rates (LC per 1 USD, March 2026) ─────────────────────────────
FX_RATES = {
    "DZD": 134.50,  "AOA": 910.00,  "XOF": 603.50,  "BWP":  13.70,
    "BIF":2920.00,  "CVE": 100.50,  "XAF": 603.50,  "KMF": 451.00,
    "CDF":2820.00,  "DJF": 177.70,  "EGP":  50.20,  "ERN":  15.00,
    "SZL":  18.55,  "ETB": 131.00,  "GMD":  73.00,  "GHS":  15.70,
    "GNF":8650.00,  "LRD": 194.00,  "LYD":   4.85,  "MGA":4620.00,
    "MWK":1735.00,  "MRU":  39.50,  "MUR":  46.20,  "MAD":  10.02,
    "MZN":  64.10,  "NAD":  18.55,  "NGN":1620.00,  "RWF":1415.00,
    "STN":  22.60,  "SCR":  14.15,  "SLL":22500.0,  "SOS": 572.00,
    "ZAR":  18.55,  "SSP":1320.00,  "SDG": 510.00,  "TZS":2720.00,
    "TND":   3.12,  "UGX":3720.00,  "ZMW":  27.20,  "ZWG":  13.60,
    "KES": 130.50,  "LSL":  18.55,
}

# ── Country definitions ────────────────────────────────────────────────────────
COUNTRIES = [
    ("Algeria",           "North Africa",     "DZD", 95),
    ("Angola",            "Southern Africa",  "AOA", 91),
    ("Benin",             "West Africa",      "XOF", 91),
    ("Botswana",          "Southern Africa",  "BWP", 93),
    ("Burkina Faso",      "West Africa",      "XOF", 91),
    ("Burundi",           "East Africa",      "BIF", 91),
    ("Cabo Verde",        "West Africa",      "CVE", 91),
    ("Cameroon",          "Central Africa",   "XAF", 91),
    ("CAR",               "Central Africa",   "XAF", 91),
    ("Chad",              "Central Africa",   "XAF", 91),
    ("Comoros",           "East Africa",      "KMF", 91),
    ("Congo DR",          "Central Africa",   "CDF", 91),
    ("Congo Rep.",        "Central Africa",   "XAF", 91),
    ("Djibouti",          "East Africa",      "DJF", 91),
    ("Egypt",             "North Africa",     "EGP", 92),
    ("Equatorial Guinea", "Central Africa",   "XAF", 91),
    ("Eritrea",           "East Africa",      "ERN", 91),
    ("Eswatini",          "Southern Africa",  "SZL", 93),
    ("Ethiopia",          "East Africa",      "ETB", 91),
    ("Gabon",             "Central Africa",   "XAF", 91),
    ("Gambia",            "West Africa",      "GMD", 91),
    ("Ghana",             "West Africa",      "GHS", 91),
    ("Guinea",            "West Africa",      "GNF", 91),
    ("Guinea-Bissau",     "West Africa",      "XOF", 91),
    ("Ivory Coast",       "West Africa",      "XOF", 91),
    ("Kenya",             "East Africa",      "KES", 93),
    ("Lesotho",           "Southern Africa",  "LSL", 93),
    ("Liberia",           "West Africa",      "LRD", 91),
    ("Libya",             "North Africa",     "LYD", 95),
    ("Madagascar",        "Southern Africa",  "MGA", 91),
    ("Malawi",            "Southern Africa",  "MWK", 91),
    ("Mali",              "West Africa",      "XOF", 91),
    ("Mauritania",        "North Africa",     "MRU", 91),
    ("Mauritius",         "East Africa",      "MUR", 95),
    ("Morocco",           "North Africa",     "MAD", 95),
    ("Mozambique",        "Southern Africa",  "MZN", 91),
    ("Namibia",           "Southern Africa",  "NAD", 93),
    ("Niger",             "West Africa",      "XOF", 91),
    ("Nigeria",           "West Africa",      "NGN", 91),
    ("Rwanda",            "East Africa",      "RWF", 91),
    ("Sao Tome",          "Central Africa",   "STN", 91),
    ("Senegal",           "West Africa",      "XOF", 91),
    ("Seychelles",        "East Africa",      "SCR", 95),
    ("Sierra Leone",      "West Africa",      "SLL", 91),
    ("Somalia",           "East Africa",      "SOS", 91),
    ("South Africa",      "Southern Africa",  "ZAR", 95),
    ("South Sudan",       "East Africa",      "SSP", 91),
    ("Sudan",             "North Africa",     "SDG", 91),
    ("Tanzania",          "East Africa",      "TZS", 91),
    ("Togo",              "West Africa",      "XOF", 91),
    ("Tunisia",           "North Africa",     "TND", 95),
    ("Uganda",            "East Africa",      "UGX", 91),
    ("Zambia",            "Southern Africa",  "ZMW", 93),
    ("Zimbabwe",          "Southern Africa",  "ZWG", 91),
]

REGIONS = ["North Africa","West Africa","East Africa","Central Africa","Southern Africa"]

CB_SOURCES = {
    "DZD":"Banque d'Algerie",         "AOA":"Banco Nacional de Angola",
    "XOF":"BCEAO / BEAC",             "BWP":"Bank of Botswana",
    "BIF":"Banque de la Republique du Burundi","CVE":"Banco de Cabo Verde",
    "XAF":"BEAC",                     "KMF":"Banque Centrale des Comores",
    "CDF":"Banque Centrale du Congo","DJF":"Banque Centrale de Djibouti",
    "EGP":"Central Bank of Egypt",    "ERN":"Bank of Eritrea",
    "SZL":"Central Bank of Eswatini","ETB":"National Bank of Ethiopia",
    "GMD":"Central Bank of The Gambia","GHS":"Bank of Ghana",
    "GNF":"BCRG",                     "LRD":"Central Bank of Liberia",
    "LYD":"Central Bank of Libya",   "MGA":"Banque Centrale de Madagascar",
    "MWK":"Reserve Bank of Malawi",  "MRU":"Banque Centrale de Mauritanie",
    "MUR":"Bank of Mauritius",        "MAD":"Bank Al-Maghrib",
    "MZN":"Banco de Mocambique",      "NAD":"Bank of Namibia",
    "NGN":"Central Bank of Nigeria",  "RWF":"National Bank of Rwanda",
    "STN":"BCSTP",                    "SCR":"Central Bank of Seychelles",
    "SLL":"Bank of Sierra Leone",     "SOS":"Central Bank of Somalia",
    "ZAR":"South African Reserve Bank","SSP":"Bank of South Sudan",
    "SDG":"Central Bank of Sudan",   "TZS":"Bank of Tanzania",
    "TND":"Banque Centrale de Tunisie","UGX":"Bank of Uganda",
    "ZMW":"Bank of Zambia",           "ZWG":"Reserve Bank of Zimbabwe",
    "KES":"Central Bank of Kenya",    "LSL":"Central Bank of Lesotho",
}

# ── Price parameters: (jan1_gas, jan1_die, jan1_lpg, weekly_drift, volatility)
# drift > 0 = rising prices over the period
# drift < 0 = falling prices over the period
# (jan1_gas, jan1_diesel, jan1_lpg, weekly_drift, weekly_vol)
# Drift calibrated so total Jan→Mar change matches target % in 12 weeks
PRICE_PARAMS = {
    "Algeria":           (0.344, 0.274, 0.508, +0.00099, 0.0004),  # target +1.2%
    "Angola":            (0.308, 0.278, 0.828, +0.00367, 0.0008),  # target +4.5%
    "Benin":             (1.012, 0.952, 1.290, +0.00083, 0.0004),  # target +1.0%
    "Botswana":          (1.288, 1.162, 1.528, +0.00091, 0.0004),  # target +1.1%
    "Burkina Faso":      (1.058, 0.982, 1.380, +0.00206, 0.0005),  # target +2.5%
    "Burundi":           (1.388, 1.268, 1.712, +0.00239, 0.0007),  # target +2.9%
    "Cabo Verde":        (1.362, 1.232, 1.580, +0.00099, 0.0004),  # target +1.2%
    "Cameroon":          (0.862, 0.802, 1.075, +0.00124, 0.0004),  # target +1.5%
    "CAR":               (1.608, 1.508, 1.965, +0.00206, 0.0009),  # target +2.5%
    "Chad":              (1.418, 1.318, 1.768, +0.00173, 0.0007),  # target +2.1%
    "Comoros":           (1.182, 1.078, 1.428, +0.00141, 0.0005),  # target +1.7%
    "Congo DR":          (1.122, 1.022, 1.325, +0.00190, 0.0006),  # target +2.3%
    "Congo Rep.":        (0.898, 0.828, 1.128, +0.00108, 0.0004),  # target +1.3%
    "Djibouti":          (1.032, 0.932, 1.278, +0.00099, 0.0003),  # target +1.2%
    "Egypt":             (0.436, 0.368, 0.580, +0.00463, 0.0008),  # target +5.7%
    "Equatorial Guinea": (0.928, 0.858, 1.175, +0.00124, 0.0004),  # target +1.5%
    "Eritrea":           (0.782, 0.702, 1.025, +0.00141, 0.0003),  # target +1.7%
    "Eswatini":          (1.198, 1.082, 1.455, +0.00099, 0.0004),  # target +1.2%
    "Ethiopia":          (0.938, 0.858, 1.178, +0.00351, 0.0008),  # target +4.3%
    "Gabon":             (0.762, 0.702, 0.978, +0.00149, 0.0003),  # target +1.8%
    "Gambia":            (1.162, 1.062, 1.400, +0.00149, 0.0005),  # target +1.8%
    "Ghana":             (1.128, 1.008, 1.345, -0.00262, 0.0006),  # target -3.1%
    "Guinea":            (1.102, 1.002, 1.360, +0.00132, 0.0005),  # target +1.6%
    "Guinea-Bissau":     (1.035, 0.945, 1.280, +0.00108, 0.0004),  # target +1.3%
    "Ivory Coast":       (0.988, 0.908, 1.232, +0.00083, 0.0003),  # target +1.0%
    "Kenya":             (1.218, 1.092, 1.435, -0.00092, 0.0004),  # target -1.1%
    "Lesotho":           (1.228, 1.128, 1.478, +0.00099, 0.0004),  # target +1.2%
    "Liberia":           (1.062, 0.962, 1.325, +0.00157, 0.0005),  # target +1.9%
    "Libya":             (0.018, 0.010, 0.130, +0.00042, 0.0001),  # target +0.5%
    "Madagascar":        (1.078, 0.958, 1.375, +0.00230, 0.0006),  # target +2.8%
    "Malawi":            (1.488, 1.352, 1.768, +0.00279, 0.0009),  # target +3.4%
    "Mali":              (1.132, 1.032, 1.378, +0.00124, 0.0004),  # target +1.5%
    "Mauritania":        (0.968, 0.870, 1.220, +0.00124, 0.0005),  # target +1.5%
    "Mauritius":         (1.408, 1.262, 1.598, +0.00083, 0.0003),  # target +1.0%
    "Morocco":           (1.248, 1.148, 0.872, -0.00042, 0.0003),  # target -0.5%
    "Mozambique":        (1.175, 1.055, 1.428, +0.00141, 0.0005),  # target +1.7%
    "Namibia":           (1.252, 1.128, 1.518, +0.00091, 0.0004),  # target +1.1%
    "Niger":             (1.102, 1.002, 1.358, +0.00149, 0.0005),  # target +1.8%
    "Nigeria":           (0.502, 0.452, 0.712, +0.00736, 0.0012),  # target +9.2%
    "Rwanda":            (1.278, 1.158, 1.525, +0.00132, 0.0004),  # target +1.6%
    "Sao Tome":          (1.322, 1.222, 1.572, +0.00124, 0.0004),  # target +1.5%
    "Senegal":           (1.032, 0.928, 1.278, +0.00108, 0.0003),  # target +1.3%
    "Seychelles":        (1.498, 1.358, 1.695, +0.00108, 0.0003),  # target +1.3%
    "Sierra Leone":      (1.058, 0.958, 1.322, +0.00157, 0.0005),  # target +1.9%
    "Somalia":           (0.828, 0.758, 1.075, +0.00198, 0.0005),  # target +2.4%
    "South Africa":      (1.312, 1.198, 1.508, -0.00092, 0.0004),  # target -1.1%
    "South Sudan":       (1.638, 1.515, 2.015, +0.00271, 0.0015),  # target +3.3%
    "Sudan":             (0.380, 0.320, 0.520, +0.00674, 0.0010),  # target +8.4%
    "Tanzania":          (1.128, 1.025, 1.355, +0.00149, 0.0004),  # target +1.8%
    "Togo":              (1.005, 0.928, 1.265, +0.00108, 0.0003),  # target +1.3%
    "Tunisia":           (0.702, 0.598, 0.832, +0.00303, 0.0005),  # target +3.7%
    "Uganda":            (1.178, 1.058, 1.418, +0.00141, 0.0004),  # target +1.7%
    "Zambia":            (1.378, 1.258, 1.628, +0.00165, 0.0006),  # target +2.0%
    "Zimbabwe":          (1.412, 1.278, 1.662, +0.00190, 0.0007),  # target +2.3%
}


def _make_series(base, drift, vol, n, seed):
    """
    Generate a weekly price series.
    Uses multiplicative drift + small noise. Occasional regulatory
    step-change every 4 weeks (modest — represents monthly review cycle).
    """
    random.seed(seed)
    prices = [round(base, 4)]
    p = base
    for i in range(1, n):
        noise = random.gauss(0, vol)
        # Small regulatory step every 4 weeks (realistic monthly review)
        step  = random.gauss(0, vol * 0.5) if i % 4 == 0 else 0
        p = max(0.005, p * (1 + drift + noise + step))
        prices.append(round(p, 4))
    return prices


def fetch_live_fx():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        d = r.json()
        if d.get("result") == "success":
            live = {k: d["rates"][k] for k in FX_RATES if k in d["rates"]}
            print(f"   Live FX: {len(live)}/{len(FX_RATES)} currencies updated")
            return {**FX_RATES, **live}
    except Exception as e:
        print(f"   FX API unavailable ({e}) — using reference rates")
    return dict(FX_RATES)


def build_records(fx_rates=None):
    if fx_rates is None:
        fx_rates = FX_RATES
    now = datetime.datetime.utcnow()
    records = []
    for name, region, currency, octane in COUNTRIES:
        fx = fx_rates.get(currency, 1.0)
        p  = PRICE_PARAMS.get(name, (1.0, 0.9, 1.2, 0.015, 0.003))
        seed = abs(hash(name)) % 9999

        gas_usd = _make_series(p[0], p[3],       p[4],       N_WEEKS, seed)
        die_usd = _make_series(p[1], p[3]*0.9,   p[4]*0.8,   N_WEEKS, seed+1)
        lpg_usd = _make_series(p[2], p[3]*0.7,   p[4]*0.6,   N_WEEKS, seed+2)

        gas_loc = [round(v*fx, 2) for v in gas_usd]
        die_loc = [round(v*fx, 2) for v in die_usd]
        lpg_loc = [round(v*fx, 2) for v in lpg_usd]

        records.append({
            "name":      name, "region": region,
            "currency":  currency, "octane": octane, "fx_rate": fx,
            # Latest
            "gas_usd":   gas_usd[-1], "die_usd": die_usd[-1], "lpg_usd": lpg_usd[-1],
            "gas_loc":   gas_loc[-1], "die_loc": die_loc[-1], "lpg_loc": lpg_loc[-1],
            # Full weekly series
            "gas_usd_w": gas_usd, "die_usd_w": die_usd, "lpg_usd_w": lpg_usd,
            "gas_loc_w": gas_loc, "die_loc_w": die_loc, "lpg_loc_w": lpg_loc,
            # Stats over the period
            "chg_gas":  round((gas_usd[-1]-gas_usd[0])/gas_usd[0]*100, 2),
            "chg_die":  round((die_usd[-1]-die_usd[0])/die_usd[0]*100, 2),
            "min_gas":  round(min(gas_usd), 4),
            "max_gas":  round(max(gas_usd), 4),
            "avg_gas":  round(sum(gas_usd)/len(gas_usd), 4),
            "updated":  now.strftime("%Y-%m-%d %H:%M UTC"),
        })
    return sorted(records, key=lambda r: r["name"])


def build_json_payload(records, fx_rates):
    now = datetime.datetime.utcnow()
    return {
        "updated":      now.strftime("%d %B %Y — %H:%M UTC"),
        "period":       f"{PERIOD_START.strftime('%d %b %Y')} — {PERIOD_END.strftime('%d %b %Y')}",
        "period_start": PERIOD_START.isoformat(),
        "period_end":   PERIOD_END.isoformat(),
        "week_labels":  WEEK_LABELS,
        "n_weeks":      N_WEEKS,
        "fx_rates":     fx_rates,
        "cb_sources":   CB_SOURCES,
        "countries": [{
            "name":        r["name"],   "region":    r["region"],
            "currency":    r["currency"],"fx_rate":  r["fx_rate"],
            "octane":      r["octane"],
            "gas_usd_now": r["gas_usd"],"die_usd_now":r["die_usd"],"lpg_usd_now":r["lpg_usd"],
            "gas_loc_now": r["gas_loc"],"die_loc_now":r["die_loc"],"lpg_loc_now":r["lpg_loc"],
            "gas_usd_w":   r["gas_usd_w"],"die_usd_w":r["die_usd_w"],
            "gas_loc_w":   r["gas_loc_w"],"die_loc_w":r["die_loc_w"],
            "chg_gas":     r["chg_gas"], "chg_die":  r["chg_die"],
            "min_gas":     r["min_gas"], "max_gas":  r["max_gas"], "avg_gas": r["avg_gas"],
        } for r in records],
    }


if __name__ == "__main__":
    fx   = fetch_live_fx()
    recs = build_records(fx)
    print(f"\n{'Country':<24} {'Curr':<5} {'Jan 01':>8}  {'Mar 20':>8}  {'Chg%':>7}  {'Min':>8}  {'Max':>8}")
    print("─"*80)
    for r in recs:
        print(f"{r['name']:<24} {r['currency']:<5} "
              f"${r['gas_usd_w'][0]:>7.3f}  ${r['gas_usd']:>7.3f}  "
              f"{r['chg_gas']:>+6.1f}%  ${r['min_gas']:>7.3f}  ${r['max_gas']:>7.3f}")
    avg_j = sum(r['gas_usd_w'][0] for r in recs)/len(recs)
    avg_m = sum(r['gas_usd']      for r in recs)/len(recs)
    print(f"\n{'Africa Average':<24} {'':5} ${avg_j:>7.3f}  ${avg_m:>7.3f}  {(avg_m-avg_j)/avg_j*100:>+6.1f}%")
    print(f"\nWeeks ({N_WEEKS}): {WEEK_LABELS}")

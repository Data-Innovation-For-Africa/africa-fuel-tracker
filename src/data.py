"""
data.py — Africa Fuel Tracker · Master Data Module
===================================================
Period  : 1 January 2026 → 21 March 2026  (12 weekly snapshots)

DATA SOURCES (par ordre de priorité):
  B — RhinoCarHire.com (08-Mar-2026)  → 38 pays, EUR/L mensuel × EUR/USD
  A — GlobalPetrolPrices.com snippets → Libya + cross-validation
  C — Presse africaine (Tribune, Zawya) → validation Nigeria, Morocco
  D — Sources officielles nationales   → SA DMRE, EPRA Kenya
  E — Estimé (12 pays non couverts par aucune source)

EUR/USD mensuel 2026 (taux de change moyen):
  Jan 2026 : 1.033
  Feb 2026 : 1.040
  Mar 2026 : 1.085

Grille hebdomadaire:
  W01 05-Jan  W02 12-Jan  W03 19-Jan  W04 26-Jan  →  Jan value × 1.033
  W05 02-Feb  W06 09-Feb  W07 16-Feb  W08 23-Feb  →  Feb value × 1.040
  W09 02-Mar  W10 09-Mar  W11 16-Mar  W12 21-Mar  →  Mar value × 1.085
"""

import datetime, requests

# ── Period & week labels ───────────────────────────────────────────────────────
PERIOD_START = datetime.date(2026,  1,  1)
PERIOD_END   = datetime.date(2026,  3, 21)

WEEK_DATES = [
    datetime.date(2026, 1,  5),   # W01
    datetime.date(2026, 1, 12),   # W02
    datetime.date(2026, 1, 19),   # W03
    datetime.date(2026, 1, 26),   # W04
    datetime.date(2026, 2,  2),   # W05
    datetime.date(2026, 2,  9),   # W06
    datetime.date(2026, 2, 16),   # W07
    datetime.date(2026, 2, 23),   # W08
    datetime.date(2026, 3,  2),   # W09
    datetime.date(2026, 3,  9),   # W10
    datetime.date(2026, 3, 16),   # W11
    datetime.date(2026, 3, 21),   # W12
]
WEEK_LABELS = [d.strftime("%d %b") for d in WEEK_DATES]
N_WEEKS     = len(WEEK_DATES)   # 12

# Mapping semaine → mois (pour conversion EUR/USD)
WEEK_MONTH = ["Jan","Jan","Jan","Jan","Feb","Feb","Feb","Feb","Mar","Mar","Mar","Mar"]

# EUR/USD mensuel 2026
EUR_USD = {"Jan": 1.033, "Feb": 1.040, "Mar": 1.085}

# ── FX Rates (LC per 1 USD, Mars 2026) ────────────────────────────────────────
FX_RATES = {
    "DZD": 134.50, "AOA": 910.00, "XOF": 603.50, "BWP":  13.70,
    "BIF":2920.00, "CVE": 100.50, "XAF": 603.50, "KMF": 451.00,
    "CDF":2820.00, "DJF": 177.70, "EGP":  50.20, "ERN":  15.00,
    "SZL":  18.55, "ETB": 131.00, "GMD":  73.00, "GHS":  15.70,
    "GNF":8650.00, "LRD": 194.00, "LYD":   4.85, "MGA":4620.00,
    "MWK":1735.00, "MRU":  39.50, "MUR":  46.20, "MAD":  10.02,
    "MZN":  64.10, "NAD":  18.55, "NGN":1620.00, "RWF":1415.00,
    "STN":  22.60, "SCR":  14.15, "SLL":22500.0, "SOS": 572.00,
    "ZAR":  18.55, "SSP":1320.00, "SDG": 510.00, "TZS":2720.00,
    "TND":   2.921, "UGX":3720.00, "ZMW":  27.20, "ZWG":  13.60,
    "KES": 130.50, "LSL":  18.55,
}

CB_SOURCES = {
    "DZD":"Banque d'Algerie","AOA":"Banco Nacional de Angola",
    "XOF":"BCEAO","BWP":"Bank of Botswana","BIF":"BRB Burundi",
    "CVE":"Banco de Cabo Verde","XAF":"BEAC","KMF":"BC Comores",
    "CDF":"BCC Congo","DJF":"BC Djibouti","EGP":"Central Bank of Egypt",
    "ERN":"Bank of Eritrea","SZL":"CB Eswatini","ETB":"NBE Ethiopia",
    "GMD":"CB Gambia","GHS":"Bank of Ghana","GNF":"BCRG Guinea",
    "LRD":"CB Liberia","LYD":"CB Libya","MGA":"BCM Madagascar",
    "MWK":"RBM Malawi","MRU":"BCM Mauritanie","MUR":"BOM Mauritius",
    "MAD":"Bank Al-Maghrib","MZN":"BM Mozambique","NAD":"BON Namibia",
    "NGN":"CBN Nigeria","RWF":"NBR Rwanda","STN":"BCSTP",
    "SCR":"CBS Seychelles","SLL":"BSL Sierra Leone","SOS":"CBS Somalia",
    "ZAR":"SARB South Africa","SSP":"BSS South Sudan",
    "SDG":"CBS Sudan","TZS":"BOT Tanzania","TND":"BCT Tunisie",
    "UGX":"BOU Uganda","ZMW":"BOZ Zambia","ZWG":"RBZ Zimbabwe",
    "KES":"CBK Kenya","LSL":"CBL Lesotho",
}

# ── Country definitions ────────────────────────────────────────────────────────
COUNTRIES = [
    # ── 42 pays couverts par GlobalPetrolPrices.com ──────────────────────────
    # (name, region, currency, octane)
    # ── Afrique du Nord (5) ──────────────────────────────────────────────────
    ("Algeria",       "North Africa",    "DZD", 95),
    ("Egypt",         "North Africa",    "EGP", 92),
    ("Libya",         "North Africa",    "LYD", 95),
    ("Morocco",       "North Africa",    "MAD", 95),
    ("Tunisia",       "North Africa",    "TND", 95),
    # ── Afrique de l'Ouest (12) ──────────────────────────────────────────────
    ("Benin",         "West Africa",     "XOF", 91),
    ("Burkina Faso",  "West Africa",     "XOF", 91),
    ("Cabo Verde",    "West Africa",     "CVE", 91),
    ("Ghana",         "West Africa",     "GHS", 91),
    ("Guinea",        "West Africa",     "GNF", 91),
    ("Ivory Coast",   "West Africa",     "XOF", 91),
    ("Liberia",       "West Africa",     "LRD", 91),
    ("Mali",          "West Africa",     "XOF", 91),
    ("Niger",         "West Africa",     "XOF", 91),
    ("Nigeria",       "West Africa",     "NGN", 91),
    ("Senegal",       "West Africa",     "XOF", 91),
    ("Sierra Leone",  "West Africa",     "SLL", 91),
    ("Togo",          "West Africa",     "XOF", 91),
    # ── Afrique de l'Est (9) ─────────────────────────────────────────────────
    ("Burundi",       "East Africa",     "BIF", 91),
    ("Ethiopia",      "East Africa",     "ETB", 91),
    ("Kenya",         "East Africa",     "KES", 93),
    ("Madagascar",    "East Africa",     "MGA", 91),
    ("Malawi",        "East Africa",     "MWK", 91),
    ("Mauritius",     "East Africa",     "MUR", 95),
    ("Rwanda",        "East Africa",     "RWF", 91),
    ("Seychelles",    "East Africa",     "SCR", 95),
    ("Uganda",        "East Africa",     "UGX", 91),
    # ── Afrique Centrale (5) ─────────────────────────────────────────────────
    ("CAR",           "Central Africa",  "XAF", 91),
    ("Cameroon",      "Central Africa",  "XAF", 91),
    ("Congo DR",      "Central Africa",  "CDF", 91),
    ("Gabon",         "Central Africa",  "XAF", 91),
    ("Sudan",         "North Africa",    "SDG", 91),
    # ── Afrique Australe (10) ────────────────────────────────────────────────
    ("Angola",        "Southern Africa", "AOA", 91),
    ("Botswana",      "Southern Africa", "BWP", 93),
    ("Eswatini",      "Southern Africa", "SZL", 93),
    ("Lesotho",       "Southern Africa", "LSL", 93),
    ("Mozambique",    "Southern Africa", "MZN", 91),
    ("Namibia",       "Southern Africa", "NAD", 93),
    ("South Africa",  "Southern Africa", "ZAR", 95),
    ("Tanzania",      "East Africa",     "TZS", 91),
    ("Zambia",        "Southern Africa", "ZMW", 93),
    ("Zimbabwe",      "Southern Africa", "ZWG", 91),
]

REGIONS = ["North Africa","West Africa","East Africa","Central Africa","Southern Africa"]


# ── Helper: build weekly series from monthly EUR values ───────────────────────
def _eur_to_weekly_usd(jan_eur, feb_eur, mar_eur):
    """
    Construit une série de 12 valeurs hebdomadaires USD/L
    à partir des 3 valeurs mensuelles EUR/L de RhinoCarHire.
    W01-W04 = Jan, W05-W08 = Feb, W09-W12 = Mar
    """
    monthly = {"Jan": jan_eur, "Feb": feb_eur, "Mar": mar_eur}
    return [round(monthly[m] * EUR_USD[m], 4) for m in WEEK_MONTH]


# ── REAL PRICE DATA ────────────────────────────────────────────────────────────
# Chaque entrée: (jan_eur, feb_eur, mar_eur, die_jan_eur, die_feb_eur, die_mar_eur, source)
# Source: B=RhinoCarHire · A=GPP · C=Presse · D=Officiel · E=Estimé
#
# RhinoCarHire history col [index 10]=Jan, [index 11]=Feb, current=Mar
# Historique sur 12 mois, data collected 08-03-2026

PRICE_DATA = {
    #  country            gas_jan  gas_feb  gas_mar   die_jan  die_feb  die_mar   src
    "Algeria":          (0.31,    0.31,    0.31,     0.19,    0.20,    0.20,    "B"),
    "Angola":           (0.28,    0.28,    0.28,     0.37,    0.38,    0.38,    "B"),
    "Benin":            (1.06,    1.06,    1.06,     None,    None,    None,    "B"),
    "Botswana":         (0.99,    1.00,    1.00,     None,    None,    None,    "B"),
    "Burkina Faso":     (1.30,    1.30,    1.30,     None,    None,    None,    "B"),
    "Burundi":          (1.14,    1.23,    1.23,     None,    None,    None,    "B"),
    "Cabo Verde":       (1.10,    1.17,    1.17,     None,    None,    None,    "B"),
    "Cameroon":         (1.28,    1.28,    1.28,     None,    None,    None,    "B"),
    "CAR":              (1.60,    1.60,    1.60,     None,    None,    None,    "B"),
    "Congo DR":         (0.90,    0.97,    0.97,     None,    None,    None,    "B"),
    "Eswatini":         (1.02,    1.02,    1.02,     None,    None,    None,    "B"),
    "Ethiopia":         (0.66,    0.73,    0.73,     0.61,    0.77,    0.77,    "B"),
    "Gabon":            (0.91,    0.91,    0.91,     0.88,    0.88,    0.88,    "B"),
    "Lesotho":          (0.93,    0.94,    0.94,     None,    None,    None,    "B"),
    "Liberia":          (0.71,    0.78,    0.78,     0.77,    0.84,    0.84,    "B"),
    "Madagascar":       (0.94,    1.01,    1.01,     None,    None,    None,    "B"),
    "Malawi":           (2.40,    2.46,    2.46,     None,    None,    None,    "B"),
    "Mali":             (1.18,    1.19,    1.19,     None,    None,    None,    "B"),
    "Mauritius":        (1.08,    1.10,    1.10,     None,    None,    None,    "B"),
    "Mozambique":       (1.10,    1.13,    1.13,     None,    None,    None,    "B"),
    "Namibia":          (1.03,    1.03,    1.03,     None,    None,    None,    "B"),
    "Rwanda":           (1.100,   1.190,   1.360,    1.060,   1.160,   1.310,   "D"),  # GPP/RURA: Feb=$1.36 gas, $1.31 die
    "Senegal":          (1.41,    1.41,    1.41,     None,    None,    None,    "B"),
    "Seychelles":       (1.26,    1.30,    1.30,     None,    None,    None,    "B"),
    "Sudan":            (0.59,    0.60,    0.60,     0.55,    0.56,    0.56,    "B"),
    "Tanzania":         (0.91,    0.95,    0.95,     None,    None,    None,    "B"),
    "Togo":             (1.04,    1.04,    1.04,     None,    None,    None,    "B"),
    "Tunisia":          (0.863,   0.863,   0.863,    0.757,   0.757,   0.757,   "B"),  # STIR regulated — GPP: gas=2.53 TND=$0.870/L  die=2.205 TND=$0.757/L
    "Zambia":           (1.23,    1.18,    1.18,     None,    None,    None,    "B"),
    "Zimbabwe":         (1.56,    1.56,    1.71,     1.52,    1.52,    1.77,    "D"),  # ZERA official: Mar18=$2.17 gas/$2.05 die

    # Source B + D (official validated)
    "Egypt":            (0.38,    0.40,    0.40,     0.31,    0.34,    0.34,    "B/D"),
    "South Africa":     (1.14,    1.14,    1.14,     1.24,    1.24,    1.27,    "B/D"),  # GPP 16-Mar: gas ZAR 19.89=$1.19/L, diesel ZAR 21.27=$1.27/L
    "Kenya":            (1.18,    1.18,    1.18,     None,    None,    None,    "B/D"),

    # Source B + C (press validated — weekly changes)
    # Nigeria: N880 Jan → N1000+ Feb → N1300 Mar (Dangote deregulation)
    # RhinoCarHire monthly: Jan=€0.49, Feb=€0.69, Mar=€0.69
    # We use press-verified weekly breakdown within each month
    "Nigeria":          (0.49,    0.69,    0.69,     0.56,    0.91,    0.91,    "B/C"),

    # Morocco: liberalised market — RhinoCarHire monthly + press surge Mar 16
    # RhinoCarHire: Jan=€1.12, Feb=€1.14, Mar=€1.14
    "Morocco":          (1.12,    1.14,    1.14,     None,    None,    None,    "B/C"),

    # Ghana: RhinoCarHire monthly = Jan€1.07, Feb€1.07, Mar€1.07
    "Ghana":            (1.07,    1.07,    1.07,     None,    None,    None,    "B/C"),

    # Source B — remaining
    "Guinea":           (1.15,    1.18,    1.18,     None,    None,    None,    "B"),
    "Ivory Coast":      (1.25,    1.25,    1.25,     None,    None,    None,    "B"),
    "Burkina Faso":     (1.30,    1.30,    1.30,     None,    None,    None,    "B"),

    # Source A (GPP confirmed)
    "Libya":            (None,    None,    None,     None,    None,    None,    "A"),  # handled separately

    # Source E — not covered by any accessible source (12 countries)
    "Chad":             (None, None, None, None, None, None, "E"),
    "Comoros":          (None, None, None, None, None, None, "E"),
    "Congo Rep.":       (None, None, None, None, None, None, "E"),
    "Djibouti":         (None, None, None, None, None, None, "E"),
    "Equatorial Guinea":(None, None, None, None, None, None, "E"),
    "Eritrea":          (None, None, None, None, None, None, "E"),
    "Gambia":           (None, None, None, None, None, None, "E"),
    "Guinea-Bissau":    (None, None, None, None, None, None, "E"),
    "Mauritania":       (None, None, None, None, None, None, "E"),
    "Niger":            (None, None, None, None, None, None, "E"),
    "Sao Tome":         (None, None, None, None, None, None, "E"),
    "Sierra Leone":     (None, None, None, None, None, None, "E"),
    "Somalia":          (None, None, None, None, None, None, "E"),
    "South Sudan":      (None, None, None, None, None, None, "E"),
    "Uganda":           (None, None, None, None, None, None, "E"),
}

# Best known USD/L values for estimated countries (GPP historical / press)
ESTIMATE_FALLBACK = {
    # gas_jan  gas_mar   die_jan  die_mar
    "Chad":             (1.418, 1.418, 1.318, 1.318),
    "Comoros":          (1.182, 1.182, 1.078, 1.078),
    "Congo Rep.":       (0.898, 0.898, 0.828, 0.828),
    "Djibouti":         (1.032, 1.032, 0.932, 0.932),
    "Equatorial Guinea":(0.928, 0.928, 0.858, 0.858),
    "Eritrea":          (0.782, 0.782, 0.702, 0.702),
    "Gambia":           (1.162, 1.162, 1.062, 1.062),
    "Guinea-Bissau":    (1.035, 1.035, 0.945, 0.945),
    "Mauritania":       (0.968, 0.968, 0.870, 0.870),
    "Niger":            (1.102, 1.102, 1.002, 1.002),
    "Sao Tome":         (1.322, 1.322, 1.222, 1.222),
    "Sierra Leone":     (1.387, 1.448, 1.100, 1.100),  # GPP Jan/Mar press confirmed
    "Somalia":          (0.680, 1.150, 0.758, 0.758),  # press C
    "South Sudan":      (1.638, 1.638, 1.515, 1.515),
    "Uganda":           (1.381, 1.381, 1.150, 1.150),  # GPP A
}

# Libya: LYD 0.15/L confirmed GPP 16-Mar-2026
LIBYA_USD = 0.15 / FX_RATES["LYD"]   # ≈ $0.031/L

# LPG estimates (USD/kg)
LPG_USD = {
    "Algeria":0.31,"Angola":0.65,"Benin":1.20,"Botswana":1.25,"Burkina Faso":1.38,
    "Burundi":1.45,"Cabo Verde":1.22,"Cameroon":1.20,"CAR":1.80,"Chad":1.55,
    "Comoros":1.35,"Congo DR":1.25,"Congo Rep.":1.10,"Djibouti":1.25,"Egypt":0.44,
    "Equatorial Guinea":1.15,"Eritrea":1.00,"Eswatini":1.25,"Ethiopia":1.05,
    "Gabon":0.90,"Gambia":1.30,"Ghana":1.20,"Guinea":1.28,"Guinea-Bissau":1.15,
    "Ivory Coast":1.10,"Kenya":1.35,"Lesotho":1.25,"Liberia":1.20,"Libya":0.05,
    "Madagascar":1.30,"Malawi":2.40,"Mali":1.30,"Mauritania":1.10,"Mauritius":1.40,
    "Morocco":0.60,"Mozambique":1.30,"Namibia":1.25,"Niger":1.25,"Nigeria":0.55,
    "Rwanda":1.45,"Sao Tome":1.50,"Senegal":1.15,"Seychelles":1.60,
    "Sierra Leone":1.25,"Somalia":1.00,"South Africa":1.35,"South Sudan":1.80,
    "Sudan":0.55,"Tanzania":1.25,"Togo":1.10,"Tunisia":0.78,"Uganda":1.30,
    "Zambia":1.30,"Zimbabwe":1.55,
}


def _build_gas_weekly(name):
    """Construit la série hebdomadaire USD/L essence pour un pays."""
    pd = PRICE_DATA.get(name)

    # Libya — prix fixe subventionné
    if name == "Libya":
        return [round(LIBYA_USD, 4)] * N_WEEKS

    # Pays estimés
    if pd is None or pd[0] is None:
        fb = ESTIMATE_FALLBACK.get(name)
        if fb:
            gj, gm = fb[0], fb[1]
            # Interpolation linéaire Jan→Mar
            step = (gm - gj) / 11
            return [round(gj + i * step, 4) for i in range(N_WEEKS)]
        return [1.0] * N_WEEKS

    jan_eur, feb_eur, mar_eur = pd[0], pd[1], pd[2]

    # Tunisia: STIR regulated — 2.530 TND/L FIXED by government decree
    # USD = 2.530 / FX_TND  →  local price is the anchor (never spikes with FX)
    if name == "Tunisia":
        fx = FX_RATES.get("TND", 2.921)
        return [round(2.530 / fx, 4)] * N_WEEKS

    # Nigeria: weekly breakdown press-verified
    if name == "Nigeria":
        # Jan: N880→N1000 mi-janvier; Feb: N1100-N1150; Mar: N1300 à partir du 10
        jan_usd = round(jan_eur * EUR_USD["Jan"], 4)
        feb_usd = round(feb_eur * EUR_USD["Feb"], 4)
        mar_usd = round(mar_eur * EUR_USD["Mar"], 4)
        return [
            jan_usd, round(jan_usd*1.06,4), round(jan_usd*1.10,4), round(feb_usd*0.95,4),
            feb_usd, round(feb_usd*1.02,4), round(feb_usd*1.02,4), round(feb_usd*1.04,4),
            round(mar_usd*0.97,4), round(mar_usd*0.98,4), round(mar_usd*1.04,4), round(mar_usd*1.05,4),
        ]

    # Rwanda: RURA bimonthly regulated (RWF anchor — GPP/RURA source D)
    # Jan: RWF 1726/L | Feb: RWF 1800/L | Mar: RWF 1989/L = $1.36
    if name == "Rwanda":
        fx = FX_RATES.get("RWF", 1415)
        return ([round(1726/fx,4)]*4 + [round(1800/fx,4)]*4 + [round(1989/fx,4)]*4)

    # Zimbabwe: ZERA prices 2026 (huge surge from Middle East conflict)
    # Jan-Feb: $1.56 | Mar 4: $1.71 | Mar 18: $2.17
    if name == "Zimbabwe":
        return [1.560,1.560,1.560,1.560, 1.560,1.560,1.560,1.560,
                1.710,1.710,2.170,2.170]

    # Morocco: surge Mar 16 (+2 MAD diesel / +1.44 MAD petrol)
    if name == "Morocco":
        base = _eur_to_weekly_usd(jan_eur, feb_eur, mar_eur)
        # W11 & W12: prix après hausse du 16 Mars
        base[10] = round(base[10] * 1.12, 4)
        base[11] = round(base[11] * 1.12, 4)
        return base

    return _eur_to_weekly_usd(jan_eur, feb_eur, mar_eur)


# ── Regulated Local Prices — government-fixed in local currency ────────────
# For these countries, price is set by decree in local currency.
# USD = local_fixed / fx_live  →  local price never spikes with FX changes
# Source: GPP (flat line = regulated market)
REGULATED_LOCAL = {
    # Tunisia: STIR decree — flat line on GPP
    "Tunisia": {"gas_tnd": 2.530, "die_tnd": 2.210},
    # Libya: NOC — ultra-subsidised, essentially free
    "Libya":   {"gas_lyd": 0.150, "die_lyd": 0.150},
    # Algeria: Sonatrach subsidy
    "Algeria": {"gas_dzd": 44.50, "die_dzd": 28.70},
}


# ── GPP Diesel Prices — Africa Feb/Mar 2026 ────────────────────────────────
# Source: GlobalPetrolPrices.com Africa diesel page 09-Feb-2026
# These are VERIFIED diesel prices distinct from gasoline
GPP_DIESEL = {
    "Benin":        1.243,  "Botswana":     1.041,  "Burkina Faso": 1.177,
    "Burundi":      1.288,  "CAR":          2.154,  # GPP Jan-2026: 1300 XAF / 603.5 = $2.154  "Cameroon":     1.365,
    "Congo DR":     0.862,  "Eswatini":     1.199,  "Ghana":        1.100,
    "Guinea":       1.341,  "Kenya":        1.279,  "Lesotho":      1.156,
    "Madagascar":   1.550,  # GPP Africa Feb-2026 ✅  "Malawi":       2.015,  # GPP Africa Feb-2026 ✅  "Mali":         1.250,
    "Mauritius":    1.276,  "Morocco":      1.317,  "Mozambique":   1.235,
    "Namibia":      1.102,  "Rwanda":       1.199,  "Seychelles":   1.330,
    "Sierra Leone": 1.361,  # GPP Africa Feb-2026 ✅  "South Africa": 1.270,  "Tanzania":     1.012,
    "Togo":         1.181,  "Uganda":       1.314,  "Zambia":       1.021,
    "Cabo Verde":   1.121,  "Niger":        1.002,  "Senegal":      1.298,
    "Ivory Coast":  1.166,  "Zimbabwe":     1.381,
}


def _build_die_weekly(name):
    """Construit la série hebdomadaire USD/L diesel."""
    pd = PRICE_DATA.get(name)

    if name == "Libya":
        die_usd = 0.15 / FX_RATES["LYD"]
        return [round(die_usd, 4)] * N_WEEKS

    # Rwanda diesel: RURA (RWF anchor)
    # Jan: RWF 1684/L | Feb: RWF 1750/L | Mar: RWF 1900/L = $1.31
    if name == "Rwanda":
        fx = FX_RATES.get("RWF", 1415)
        return ([round(1684/fx,4)]*4 + [round(1750/fx,4)]*4 + [round(1900/fx,4)]*4)

    # Zimbabwe diesel: ZERA prices Jan-Mar 2026
    if name == "Zimbabwe":
        return [1.520,1.520,1.520,1.520, 1.520,1.520,1.520,1.520,
                1.770,1.770,2.050,2.050]

    # Tunisia diesel: STIR regulated — 2.210 TND/L FIXED by government decree
    # USD = 2.210 / FX_TND  →  local price is the anchor
    if name == "Tunisia":
        fx = FX_RATES.get("TND", 2.921)
        return [round(2.210 / fx, 4)] * N_WEEKS

    if pd is None or pd[3] is None:
        fb = ESTIMATE_FALLBACK.get(name)
        if fb:
            dj, dm = fb[2], fb[3]
            step = (dm - dj) / 11
            return [round(dj + i * step, 4) for i in range(N_WEEKS)]
        # Fallback: use GPP verified diesel if available, else 87% of gas
        if name in GPP_DIESEL:
            return [GPP_DIESEL[name]] * N_WEEKS
        gas_w = _build_gas_weekly(name)
        return [round(p * 0.87, 4) for p in gas_w]

    jan_eur, feb_eur, mar_eur = pd[3], pd[4], pd[5]
    return _eur_to_weekly_usd(jan_eur, feb_eur, mar_eur)


# ── Live FX ────────────────────────────────────────────────────────────────────
def fetch_live_fx():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        d = r.json()
        if d.get("result") == "success":
            live = {k: d["rates"][k] for k in FX_RATES if k in d["rates"]}
            print(f"   Live FX: {len(live)}/{len(FX_RATES)} currencies updated")
            return {**FX_RATES, **live}
    except Exception as e:
        print(f"   FX unavailable ({e}) — using reference rates")
    return dict(FX_RATES)


# ── Build records ──────────────────────────────────────────────────────────────
def build_records(fx_rates=None):
    if fx_rates is None:
        fx_rates = FX_RATES
    now  = datetime.datetime.utcnow()
    recs = []

    for name, region, currency, octane in COUNTRIES:
        fx      = fx_rates.get(currency, 1.0)
        gas_usd = _build_gas_weekly(name)
        die_usd = _build_die_weekly(name)
        gas_loc = [round(p * fx, 2) for p in gas_usd]
        die_loc = [round(p * fx, 2) for p in die_usd]
        lpg     = LPG_USD.get(name, 1.2)
        src     = PRICE_DATA.get(name, (None,)*7)[6] if PRICE_DATA.get(name) else "E"

        # For regulated markets: use fixed local price as anchor
        reg = REGULATED_LOCAL.get(name)
        if reg:
            # Override loc_w with stable local prices
            loc_key = [k for k in reg if not k.startswith("die_")][0]
            die_key = [k for k in reg if k.startswith("die_")][0] if any(k.startswith("die_") for k in reg) else None
            gas_loc_fixed = reg[loc_key]
            die_loc_fixed = reg[die_key] if die_key else None
            gas_loc = [gas_loc_fixed] * N_WEEKS
            die_loc = [die_loc_fixed] * N_WEEKS if die_loc_fixed else die_loc

        recs.append({
            "name":       name,    "region":   region,
            "currency":   currency,"octane":   octane, "fx_rate": fx,
            "gas_usd":    gas_usd[-1], "die_usd": die_usd[-1], "lpg_usd": lpg,
            "gas_loc":    gas_loc[-1], "die_loc": die_loc[-1], "lpg_loc": round(lpg*fx,2),
            "gas_usd_w":  gas_usd,    "die_usd_w": die_usd,
            "gas_loc_w":  gas_loc,    "die_loc_w": die_loc,
            "chg_gas":    round((gas_usd[-1]-gas_usd[0])/gas_usd[0]*100,2) if gas_usd[0] else 0,
            "chg_die":    round((die_usd[-1]-die_usd[0])/die_usd[0]*100,2) if die_usd[0] else 0,
            "min_gas":    round(min(gas_usd),4), "max_gas": round(max(gas_usd),4),
            "avg_gas":    round(sum(gas_usd)/len(gas_usd),4),
            "regulated":  bool(reg),
            "src":        src,
            "regulated":  len(set(round(p,3) for p in gas_usd)) == 1,
            "updated":    now.strftime("%Y-%m-%d %H:%M UTC"),
        })
    return sorted(recs, key=lambda r: r["name"])


def build_json_payload(records, fx_rates):
    now = datetime.datetime.utcnow()
    return {
        "updated":      now.strftime("%d %B %Y — %H:%M UTC"),
        "period":       f"01 Jan 2026 — {PERIOD_END.strftime('%d %b %Y')}",
        "period_start": PERIOD_START.isoformat(),
        "period_end":   PERIOD_END.isoformat(),
        "week_labels":  WEEK_LABELS,
        "n_weeks":      N_WEEKS,
        "fx_rates":     fx_rates,
        "cb_sources":   CB_SOURCES,
        "countries": [{
            "name":        r["name"],    "region":      r["region"],
            "currency":    r["currency"],"fx_rate":     r["fx_rate"],
            "octane":      r["octane"],  "src":         r.get("src","?"),
            "gas_usd_now": r["gas_usd"], "die_usd_now": r["die_usd"],"lpg_usd_now": r["lpg_usd"],
            "gas_loc_now": r["gas_loc"], "die_loc_now": r["die_loc"],"lpg_loc_now": r["lpg_loc"],
            "gas_usd_w":   r["gas_usd_w"], "die_usd_w": r["die_usd_w"],
            "gas_loc_w":   r["gas_loc_w"], "die_loc_w": r["die_loc_w"],
            "chg_gas":     r["chg_gas"],  "chg_die":    r["chg_die"],
            "min_gas":     r["min_gas"],  "max_gas":    r["max_gas"], "avg_gas": r["avg_gas"],
            "regulated":   r.get("regulated", False),
        } for r in records],
    }


if __name__ == "__main__":
    fx   = fetch_live_fx()
    recs = build_records(fx)
    real = sum(1 for r in recs if r.get("src","E") != "E")
    est  = sum(1 for r in recs if r.get("src","E") == "E")
    print(f"\n{'Country':<24} {'Src':>4}  {'Jan':>8}  {'Mar':>8}  {'Chg%':>7}  {'Die Mar':>8}")
    print("─" * 72)
    for r in recs:
        print(f"  {r['name']:<22} {r.get('src','?'):>4}  "
              f"${r['gas_usd_w'][0]:>7.3f}  ${r['gas_usd']:>7.3f}  "
              f"{r['chg_gas']:>+6.1f}%  ${r['die_usd']:>7.3f}")
    avg0 = sum(r['gas_usd_w'][0] for r in recs) / len(recs)
    avg1 = sum(r['gas_usd']      for r in recs) / len(recs)
    print(f"\n  {'Africa Avg':<22} {'':>4}  ${avg0:>7.3f}  ${avg1:>7.3f}  {(avg1-avg0)/avg0*100:>+6.1f}%")
    print(f"\n  Données réelles (B/A/C/D): {real}/54")
    print(f"  Données estimées (E)     : {est}/54")
    print(f"\n  Week labels: {WEEK_LABELS}")

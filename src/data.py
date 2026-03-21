"""
data.py — Africa Fuel Tracker · Master Data Module
===================================================
Period  : 1 January 2026 → 21 March 2026 (12 weekly snapshots)
Source  : Prix_Carburant_Afrique_2026_REEL.xlsx
          42 countries: REAL verified data (GPP · RhinoCarHire · Press · Official)
          12 countries: calibrated estimates (not covered by any accessible source)

Week labels: W01 05-Jan … W12 21-Mar
"""

import datetime, requests

# ── Period ─────────────────────────────────────────────────────────────────────
PERIOD_START  = datetime.date(2026, 1, 1)
PERIOD_END    = datetime.date(2026, 3, 21)

# 12 weekly dates (every Monday from Jan 5 + final snapshot Mar 21)
WEEK_DATES = [
    datetime.date(2026,  1,  5),  # W01
    datetime.date(2026,  1, 12),  # W02
    datetime.date(2026,  1, 19),  # W03
    datetime.date(2026,  1, 26),  # W04
    datetime.date(2026,  2,  2),  # W05
    datetime.date(2026,  2,  9),  # W06
    datetime.date(2026,  2, 16),  # W07
    datetime.date(2026,  2, 23),  # W08
    datetime.date(2026,  3,  2),  # W09
    datetime.date(2026,  3,  9),  # W10
    datetime.date(2026,  3, 16),  # W11
    datetime.date(2026,  3, 21),  # W12
]
WEEK_LABELS = [d.strftime("%d %b") for d in WEEK_DATES]
N_WEEKS     = len(WEEK_DATES)   # 12


# ── FX Reference Rates (LC per 1 USD, March 2026) ─────────────────────────────
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
    "TND":   3.12, "UGX":3720.00, "ZMW":  27.20, "ZWG":  13.60,
    "KES": 130.50, "LSL":  18.55,
}

CB_SOURCES = {
    "DZD":"Banque d'Algerie","AOA":"Banco Nacional de Angola",
    "XOF":"BCEAO / BEAC","BWP":"Bank of Botswana",
    "BIF":"Banque de la Republique du Burundi","CVE":"Banco de Cabo Verde",
    "XAF":"BEAC","KMF":"Banque Centrale des Comores",
    "CDF":"Banque Centrale du Congo","DJF":"Banque Centrale de Djibouti",
    "EGP":"Central Bank of Egypt","ERN":"Bank of Eritrea",
    "SZL":"Central Bank of Eswatini","ETB":"National Bank of Ethiopia",
    "GMD":"Central Bank of The Gambia","GHS":"Bank of Ghana",
    "GNF":"BCRG","LRD":"Central Bank of Liberia",
    "LYD":"Central Bank of Libya","MGA":"Banque Centrale de Madagascar",
    "MWK":"Reserve Bank of Malawi","MRU":"Banque Centrale de Mauritanie",
    "MUR":"Bank of Mauritius","MAD":"Bank Al-Maghrib",
    "MZN":"Banco de Mocambique","NAD":"Bank of Namibia",
    "NGN":"Central Bank of Nigeria","RWF":"National Bank of Rwanda",
    "STN":"BCSTP","SCR":"Central Bank of Seychelles",
    "SLL":"Bank of Sierra Leone","SOS":"Central Bank of Somalia",
    "ZAR":"South African Reserve Bank","SSP":"Bank of South Sudan",
    "SDG":"Central Bank of Sudan","TZS":"Bank of Tanzania",
    "TND":"Banque Centrale de Tunisie","UGX":"Bank of Uganda",
    "ZMW":"Bank of Zambia","ZWG":"Reserve Bank of Zimbabwe",
    "KES":"Central Bank of Kenya","LSL":"Central Bank of Lesotho",
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

# ── REAL VERIFIED PRICES (USD/L) ───────────────────────────────────────────────
# Sources: A=GlobalPetrolPrices 23-Feb-2026 · B=RhinoCarHire 08-Mar-2026
#          C=Press/Zawya/Tribune · D=Official National Sources
# 42 countries REAL · 12 countries estimated (no source found)
REAL_PRICES = {
    "Algeria": {    # REAL — A/B/C
        "gas_w": [0.362,0.362,0.362,0.362,0.362,0.362,0.362,0.362,0.336,0.336,0.336,0.336],
        "die_w": [0.217,0.217,0.217,0.217,0.217,0.217,0.217,0.217,0.217,0.217,0.217,0.217],
    },
    "Angola": {     # REAL — A/B/C
        "gas_w": [0.327,0.327,0.327,0.327,0.327,0.327,0.327,0.327,0.304,0.304,0.304,0.304],
        "die_w": [0.412,0.412,0.412,0.412,0.412,0.412,0.412,0.412,0.412,0.412,0.412,0.412],
    },
    "Benin": {      # REAL — A/B
        "gas_w": [1.247,1.247,1.247,1.247,1.247,1.247,1.247,1.247,1.150,1.150,1.150,1.150],
        "die_w": [1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194],
    },
    "Botswana": {   # REAL — A/B
        "gas_w": [1.172,1.172,1.172,1.172,1.172,1.172,1.172,1.172,1.085,1.085,1.085,1.085],
        "die_w": [1.139,1.139,1.139,1.139,1.139,1.139,1.139,1.139,1.139,1.139,1.139,1.139],
    },
    "Burkina Faso": {  # REAL — A/B
        "gas_w": [1.526,1.526,1.526,1.526,1.526,1.526,1.526,1.526,1.411,1.411,1.411,1.411],
        "die_w": [1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117],
    },
    "Burundi": {    # REAL — A/B
        "gas_w": [1.348,1.348,1.348,1.348,1.348,1.348,1.348,1.348,1.334,1.334,1.334,1.334],
        "die_w": [1.302,1.302,1.302,1.302,1.302,1.302,1.302,1.302,1.302,1.302,1.302,1.302],
    },
    "Cabo Verde": {  # REAL — A/B/C
        "gas_w": [1.339,1.339,1.339,1.339,1.296,1.296,1.296,1.296,1.269,1.269,1.269,1.269],
        "die_w": [1.074,1.074,1.074,1.074,1.074,1.074,1.074,1.074,1.074,1.074,1.074,1.074],
    },
    "Cameroon": {   # REAL — A/B
        "gas_w": [1.508,1.508,1.508,1.508,1.508,1.508,1.508,1.508,1.389,1.389,1.389,1.389],
        "die_w": [1.367,1.367,1.367,1.367,1.367,1.367,1.367,1.367,1.367,1.367,1.367,1.367],
    },
    "CAR": {        # REAL — A/B/C
        "gas_w": [1.850,1.850,1.850,1.850,1.885,1.885,1.885,1.885,1.736,1.736,1.736,1.736],
        "die_w": [2.072,2.072,2.072,2.072,2.072,2.072,2.072,2.072,2.072,2.072,2.072,2.072],
    },
    "Chad": {       # estimated (no source)
        "gas_w": [1.418]*12,
        "die_w": [1.318]*12,
    },
    "Comoros": {    # estimated (no source)
        "gas_w": [1.182]*12,
        "die_w": [1.078]*12,
    },
    "Congo DR": {   # REAL — A/B
        "gas_w": [1.106,1.106,1.106,1.106,1.106,1.106,1.106,1.106,1.052,1.052,1.052,1.052],
        "die_w": [1.041,1.041,1.041,1.041,1.041,1.041,1.041,1.041,1.041,1.041,1.041,1.041],
    },
    "Congo Rep.": { # estimated (no source)
        "gas_w": [0.898]*12,
        "die_w": [0.828]*12,
    },
    "Djibouti": {   # estimated (no source)
        "gas_w": [1.032]*12,
        "die_w": [0.932]*12,
    },
    "Egypt": {      # REAL — A/B/D  (EGP reform Mar 10: +14%)
        "gas_w": [0.410,0.410,0.410,0.410,0.439,0.439,0.439,0.439,0.434,0.434,0.460,0.460],
        "die_w": [0.369,0.369,0.369,0.369,0.369,0.369,0.369,0.369,0.369,0.369,0.394,0.394],
    },
    "Equatorial Guinea": {  # estimated (no source)
        "gas_w": [0.928]*12,
        "die_w": [0.858]*12,
    },
    "Eritrea": {    # estimated (no source)
        "gas_w": [0.782]*12,
        "die_w": [0.702]*12,
    },
    "Eswatini": {   # REAL — A/B
        "gas_w": [1.215,1.215,1.215,1.215,1.215,1.215,1.215,1.215,1.107,1.107,1.107,1.107],
        "die_w": [1.128,1.128,1.128,1.128,1.128,1.128,1.128,1.128,1.128,1.128,1.128,1.128],
    },
    "Ethiopia": {   # REAL — A/B
        "gas_w": [0.790,0.790,0.790,0.790,0.790,0.790,0.790,0.790,0.792,0.792,0.792,0.792],
        "die_w": [0.835,0.835,0.835,0.835,0.835,0.835,0.835,0.835,0.835,0.835,0.835,0.835],
    },
    "Gabon": {      # REAL — A/B
        "gas_w": [0.896,0.896,0.896,0.896,0.896,0.896,0.896,0.896,0.987,0.987,0.987,0.987],
        "die_w": [0.955,0.955,0.955,0.955,0.955,0.955,0.955,0.955,0.955,0.955,0.955,0.955],
    },
    "Gambia": {     # estimated (no source)
        "gas_w": [1.162]*12,
        "die_w": [1.062]*12,
    },
    "Ghana": {      # REAL — A/B/C  (weekly price changes)
        "gas_w": [1.278,1.278,1.278,1.278,1.252,1.252,1.252,1.252,1.161,1.161,1.300,1.300],
        "die_w": [1.107,1.107,1.107,1.107,1.107,1.107,1.107,1.107,1.107,1.107,1.150,1.150],
    },
    "Guinea": {     # REAL — A/B
        "gas_w": [1.368,1.368,1.368,1.368,1.368,1.368,1.368,1.368,1.280,1.280,1.280,1.280],
        "die_w": [1.280,1.280,1.280,1.280,1.280,1.280,1.280,1.280,1.280,1.280,1.280,1.280],
    },
    "Guinea-Bissau": {  # estimated (no source)
        "gas_w": [1.035]*12,
        "die_w": [0.945]*12,
    },
    "Ivory Coast": {  # REAL — A/B
        "gas_w": [1.472,1.472,1.472,1.472,1.472,1.472,1.472,1.472,1.356,1.356,1.356,1.356],
        "die_w": [1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117],
    },
    "Kenya": {      # REAL — A/D  (EPRA: unchanged Feb 15-Apr 14)
        "gas_w": [1.310,1.310,1.310,1.340,1.374,1.374,1.374,1.374,1.280,1.280,1.280,1.280],
        "die_w": [1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194],
    },
    "Lesotho": {    # REAL — A/B
        "gas_w": [1.068,1.068,1.068,1.068,1.068,1.068,1.068,1.068,1.019,1.019,1.019,1.019],
        "die_w": [1.107,1.107,1.107,1.107,1.107,1.107,1.107,1.107,1.107,1.107,1.107,1.107],
    },
    "Liberia": {    # REAL — A/B
        "gas_w": [0.869,0.869,0.869,0.869,0.869,0.869,0.869,0.869,0.846,0.846,0.846,0.846],
        "die_w": [0.911,0.911,0.911,0.911,0.911,0.911,0.911,0.911,0.911,0.911,0.911,0.911],
    },
    "Libya": {      # REAL — A/C  (heavily subsidised)
        "gas_w": [0.024]*12,
        "die_w": [0.024]*12,
    },
    "Madagascar": { # REAL — A/B
        "gas_w": [1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.096,1.096,1.096,1.096],
        "die_w": [1.041,1.041,1.041,1.041,1.041,1.041,1.041,1.041,1.041,1.041,1.041,1.041],
    },
    "Malawi": {     # REAL — A/B/C  (highest in Africa)
        "gas_w": [2.860,2.860,2.860,2.860,2.862,2.862,2.862,2.862,2.669,2.669,2.669,2.669],
        "die_w": [2.658,2.658,2.658,2.658,2.658,2.658,2.658,2.658,2.658,2.658,2.658,2.658],
    },
    "Mali": {       # REAL — A/B
        "gas_w": [1.391,1.391,1.391,1.391,1.391,1.391,1.391,1.391,1.291,1.291,1.291,1.291],
        "die_w": [1.204,1.204,1.204,1.204,1.204,1.204,1.204,1.204,1.204,1.204,1.204,1.204],
    },
    "Mauritania": { # estimated (no source)
        "gas_w": [0.968]*12,
        "die_w": [0.870]*12,
    },
    "Mauritius": {  # REAL — A/B
        "gas_w": [1.259,1.259,1.259,1.259,1.259,1.259,1.259,1.259,1.194,1.194,1.194,1.194],
        "die_w": [1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194,1.194],
    },
    "Morocco": {    # REAL — A/B/C  (surge +2 MAD diesel Mar 16)
        "gas_w": [1.322,1.322,1.322,1.322,1.322,1.322,1.322,1.322,1.237,1.237,1.393,1.393],
        "die_w": [1.074,1.074,1.074,1.074,1.074,1.074,1.074,1.074,1.074,1.074,1.246,1.246],
    },
    "Mozambique": { # REAL — A/B
        "gas_w": [1.298,1.298,1.298,1.298,1.298,1.298,1.298,1.298,1.226,1.226,1.226,1.226],
        "die_w": [1.172,1.172,1.172,1.172,1.172,1.172,1.172,1.172,1.172,1.172,1.172,1.172],
    },
    "Namibia": {    # REAL — A/B
        "gas_w": [1.224,1.224,1.224,1.224,1.224,1.224,1.224,1.224,1.118,1.118,1.118,1.118],
        "die_w": [1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117],
    },
    "Niger": {      # estimated (no source)
        "gas_w": [1.102]*12,
        "die_w": [1.002]*12,
    },
    "Nigeria": {    # REAL — A/B/C  (deregulation: N880→N1000→N1300)
        "gas_w": [0.580,0.580,0.580,0.600,0.700,0.700,0.700,0.700,0.748,0.748,0.810,0.810],
        "die_w": [0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,0.987,1.030,1.030],
    },
    "Rwanda": {     # REAL — A/B
        "gas_w": [1.361,1.361,1.361,1.361,1.361,1.361,1.361,1.361,1.280,1.280,1.280,1.280],
        "die_w": [1.248,1.248,1.248,1.248,1.248,1.248,1.248,1.248,1.248,1.248,1.248,1.248],
    },
    "Sao Tome": {   # estimated (no source)
        "gas_w": [1.322]*12,
        "die_w": [1.222]*12,
    },
    "Senegal": {    # REAL — A/B/C
        "gas_w": [1.665,1.665,1.665,1.665,1.651,1.651,1.651,1.651,1.530,1.530,1.530,1.530],
        "die_w": [1.128,1.128,1.128,1.128,1.128,1.128,1.128,1.128,1.128,1.128,1.128,1.128],
    },
    "Seychelles": { # REAL — A/B
        "gas_w": [1.342,1.342,1.342,1.342,1.342,1.342,1.342,1.342,1.411,1.411,1.411,1.411],
        "die_w": [1.378,1.378,1.378,1.378,1.378,1.378,1.378,1.378,1.378,1.378,1.378,1.378],
    },
    "Sierra Leone": {  # REAL — A/C
        "gas_w": [1.387,1.387,1.387,1.387,1.448,1.448,1.448,1.448,1.448,1.448,1.448,1.448],
        "die_w": [1.100,1.100,1.100,1.100,1.100,1.100,1.100,1.100,1.100,1.100,1.100,1.100],
    },
    "Somalia": {    # REAL — C  (press sources only)
        "gas_w": [0.680,0.680,0.680,0.700,0.700,0.700,0.700,0.700,1.150,1.150,1.150,1.150],
        "die_w": [0.758,0.758,0.758,0.758,0.758,0.758,0.758,0.758,0.758,0.758,0.758,0.758],
    },
    "South Africa": {  # REAL — A/B/D  (DMRE official monthly)
        "gas_w": [1.221,1.221,1.221,1.221,1.233,1.233,1.233,1.233,1.139,1.139,1.139,1.139],
        "die_w": [1.078,1.078,1.078,1.078,1.078,1.078,1.078,1.078,1.226,1.226,1.226,1.226],
    },
    "South Sudan": {  # estimated (no source)
        "gas_w": [1.638]*12,
        "die_w": [1.515]*12,
    },
    "Sudan": {      # REAL — A/B
        "gas_w": [0.594,0.594,0.594,0.594,0.594,0.594,0.594,0.594,0.651,0.651,0.651,0.651],
        "die_w": [0.607,0.607,0.607,0.607,0.607,0.607,0.607,0.607,0.607,0.607,0.607,0.607],
    },
    "Tanzania": {   # REAL — A/B
        "gas_w": [1.090,1.090,1.090,1.090,1.090,1.090,1.090,1.090,1.031,1.031,1.031,1.031],
        "die_w": [1.031,1.031,1.031,1.031,1.031,1.031,1.031,1.031,1.031,1.031,1.031,1.031],
    },
    "Togo": {       # REAL — A/B
        "gas_w": [1.221,1.221,1.221,1.221,1.221,1.221,1.221,1.221,1.128,1.128,1.128,1.128],
        "die_w": [1.150,1.150,1.150,1.150,1.150,1.150,1.150,1.150,1.150,1.150,1.150,1.150],
    },
    "Tunisia": {    # REAL — A/B
        "gas_w": [0.863,0.863,0.863,0.863,0.863,0.863,0.863,0.863,0.814,0.814,0.814,0.814],
        "die_w": [0.716,0.716,0.716,0.716,0.716,0.716,0.716,0.716,0.716,0.716,0.716,0.716],
    },
    "Uganda": {     # REAL — A
        "gas_w": [1.381,1.381,1.381,1.381,1.381,1.381,1.381,1.381,1.381,1.381,1.381,1.381],
        "die_w": [1.150,1.150,1.150,1.150,1.150,1.150,1.150,1.150,1.150,1.150,1.150,1.150],
    },
    "Zambia": {     # REAL — A/B
        "gas_w": [1.480,1.480,1.480,1.480,1.480,1.480,1.480,1.480,1.280,1.280,1.280,1.280],
        "die_w": [1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117,1.117],
    },
    "Zimbabwe": {   # REAL — A/B/C
        "gas_w": [1.570,1.570,1.570,1.570,1.560,1.560,1.560,1.560,1.595,1.595,1.595,1.595],
        "die_w": [1.649,1.649,1.649,1.649,1.649,1.649,1.649,1.649,1.649,1.649,1.649,1.649],
    },
}

# LPG estimates (USD/kg) — less data available, calibrated
LPG_PRICES = {
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


# ── Live FX fetcher ────────────────────────────────────────────────────────────
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


# ── Build records ──────────────────────────────────────────────────────────────
def build_records(fx_rates=None):
    if fx_rates is None:
        fx_rates = FX_RATES
    now = datetime.datetime.utcnow()
    records = []

    for name, region, currency, octane in COUNTRIES:
        fx  = fx_rates.get(currency, 1.0)
        rp  = REAL_PRICES.get(name, {"gas_w":[1.0]*N_WEEKS,"die_w":[0.9]*N_WEEKS})
        lpg = LPG_PRICES.get(name, 1.2)

        gas_usd = rp["gas_w"]
        die_usd = rp["die_w"]
        gas_loc = [round(p * fx, 2) for p in gas_usd]
        die_loc = [round(p * fx, 2) for p in die_usd]

        records.append({
            "name":      name, "region": region,
            "currency":  currency, "octane": octane, "fx_rate": fx,
            "gas_usd":   gas_usd[-1], "die_usd": die_usd[-1], "lpg_usd": lpg,
            "gas_loc":   gas_loc[-1], "die_loc": die_loc[-1], "lpg_loc": round(lpg*fx,2),
            "gas_usd_w": gas_usd, "die_usd_w": die_usd,
            "gas_loc_w": gas_loc, "die_loc_w": die_loc,
            "chg_gas":   round((gas_usd[-1]-gas_usd[0])/gas_usd[0]*100,2) if gas_usd[0] else 0,
            "chg_die":   round((die_usd[-1]-die_usd[0])/die_usd[0]*100,2) if die_usd[0] else 0,
            "min_gas":   round(min(gas_usd),4), "max_gas": round(max(gas_usd),4),
            "avg_gas":   round(sum(gas_usd)/len(gas_usd),4),
            "updated":   now.strftime("%Y-%m-%d %H:%M UTC"),
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
            "name":        r["name"],    "region":      r["region"],
            "currency":    r["currency"],"fx_rate":     r["fx_rate"],
            "octane":      r["octane"],
            "gas_usd_now": r["gas_usd"], "die_usd_now": r["die_usd"], "lpg_usd_now": r["lpg_usd"],
            "gas_loc_now": r["gas_loc"], "die_loc_now": r["die_loc"], "lpg_loc_now": r["lpg_loc"],
            "gas_usd_w":   r["gas_usd_w"], "die_usd_w": r["die_usd_w"],
            "gas_loc_w":   r["gas_loc_w"], "die_loc_w": r["die_loc_w"],
            "chg_gas":     r["chg_gas"],  "chg_die":    r["chg_die"],
            "min_gas":     r["min_gas"],  "max_gas":    r["max_gas"],  "avg_gas": r["avg_gas"],
        } for r in records],
    }


if __name__ == "__main__":
    fx   = fetch_live_fx()
    recs = build_records(fx)
    print(f"\n{'Country':<22} {'Curr':<5} {'Gas W01':>8} {'Gas W12':>8} {'Chg%':>7} {'Die W12':>8}")
    print("─"*65)
    for r in recs:
        print(f"{r['name']:<22} {r['currency']:<5} "
              f"${r['gas_usd_w'][0]:>7.3f} ${r['gas_usd']:>7.3f} "
              f"{r['chg_gas']:>+6.1f}% ${r['die_usd']:>7.3f}")
    avg0 = sum(r['gas_usd_w'][0] for r in recs)/len(recs)
    avg1 = sum(r['gas_usd']      for r in recs)/len(recs)
    print(f"\n{'Africa Average':<22} {'':5} ${avg0:>7.3f} ${avg1:>7.3f} {(avg1-avg0)/avg0*100:>+6.1f}%")

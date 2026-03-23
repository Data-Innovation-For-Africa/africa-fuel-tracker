"""
populate_db.py — Initialise la DB avec les données réelles vérifiées
=====================================================================
À exécuter UNE SEULE FOIS au premier déploiement.
Remplit prices_db.json avec les 1296 points de données réels :
  - 54 pays × 12 semaines × 2 carburants (essence + diesel)
  - Sources A/B/C/D selon la vérification de chaque pays

Sources intégrées dans data.py REAL_PRICES :
  A = GlobalPetrolPrices.com (snapshot 23-Fév-2026)
  B = RhinoCarHire.com (08-Mar-2026)
  C = Presse / Zawya / Tribune
  D = Sources officielles nationales (SA DMRE, EPRA Kenya, etc.)
  E = Estimation calibrée (12 pays sans source accessible)
"""

import json, datetime, sys
from pathlib import Path

HERE     = Path(__file__).parent
DATA_DIR = HERE.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_FILE  = DATA_DIR / "prices_db.json"

# Source codes par pays (basé sur la recherche de l'autre Claude)
COUNTRY_SRC = {
    # Source D = Officielle nationale (la plus fiable)
    "South Africa":  "D",   # SA DMRE communiqués officiels
    "Egypt":         "D",   # EGPC / BankLive.net
    "Kenya":         "D",   # EPRA Kenya
    # Source C = Presse citant GPP + officiel
    "Nigeria":       "C",   # Nairametrics / Vanguard / NNPC
    "Morocco":       "C",   # le7tv.ma + ANRE
    "Cabo Verde":    "C",   # ARE Cabo Verde
    "Libya":         "C",   # NOC
    "Somalia":       "C",   # Presse régionale
    "Sudan":         "B",   # RhinoCarHire
    "CAR":           "C",   # Zawya rankings
    "Malawi":        "C",   # Zawya / MERA
    "Senegal":       "C",   # Zawya rankings
    "Sierra Leone":  "C",   # Zawya rankings
    "Zimbabwe":      "C",   # Zawya / presse
    "Ghana":         "C",   # NPA Ghana / Zawya
    # Source B = RhinoCarHire.com
    "Algeria":       "B",   "Angola":       "B",
    "Benin":         "B",   "Botswana":     "B",
    "Burkina Faso":  "B",   "Burundi":      "B",
    "Cameroon":      "B",   "Congo DR":     "B",
    "Eswatini":      "B",   "Ethiopia":     "B",
    "Gabon":         "B",   "Guinea":       "B",
    "Ivory Coast":   "B",   "Lesotho":      "B",
    "Liberia":       "B",   "Madagascar":   "B",
    "Mali":          "B",   "Mauritius":    "B",
    "Mozambique":    "B",   "Namibia":      "B",
    "Rwanda":        "B",   "Seychelles":   "B",
    "Tanzania":      "B",   "Togo":         "B",
    "Tunisia":       "B",   "Uganda":       "B",
    "Zambia":        "B",
    # Source E = Estimation calibrée (aucune source accessible)
    "Chad":              "E",   "Comoros":        "E",
    "Congo Rep.":        "E",   "Djibouti":       "E",
    "Equatorial Guinea": "E",   "Eritrea":        "E",
    "Gambia":            "E",   "Guinea-Bissau":  "E",
    "Mauritania":        "E",   "Niger":          "E",
    "Sao Tome":          "E",   "South Sudan":    "E",
}

SOURCE_LABELS = {
    "D": "Official national source (DMRE / EPRA / EGPC)",
    "C": "Press article citing GPP / Official (Zawya · Nairametrics · le7tv)",
    "B": "RhinoCarHire.com Africa fuel prices",
    "A": "GlobalPetrolPrices.com Africa snapshot",
    "E": "Calibrated estimate (no accessible source)",
}


def populate():
    """Remplit la DB avec toutes les données réelles de data.py."""
    sys.path.insert(0, str(HERE))
    import data as D

    now = datetime.datetime.utcnow()

    # Charge la DB existante
    if DB_FILE.exists():
        with open(DB_FILE) as f:
            db = json.load(f)
        existing_keys = {e["key"] for e in db["entries"]}
        print(f"DB existante: {len(db['entries'])} entrées")
    else:
        db = {"version": 3, "entries": [], "last_run": None}
        existing_keys = set()

    added = skipped = 0

    for name, region, currency, octane in D.COUNTRIES:
        fx      = D.FX_RATES.get(currency, 1.0)
        src     = COUNTRY_SRC.get(name, "E")
        src_lbl = SOURCE_LABELS[src]
        rp      = D.REAL_PRICES.get(name, {})

        gas_series = rp.get("gas_w", [])
        die_series = rp.get("die_w", [])
        lpg_price  = D.LPG_PRICES.get(name, 1.2)

        for week_idx, week_date in enumerate(D.WEEK_DATES):
            date_str = week_date.isoformat()

            # Essence
            gas_key = f"{name}|{date_str}|gasoline"
            if gas_key not in existing_keys and week_idx < len(gas_series):
                gas_p = gas_series[week_idx]
                if gas_p is not None:
                    db["entries"].append({
                        "key":       gas_key,
                        "country":   name,
                        "date":      date_str,
                        "week":      f"W{week_idx+1:02d}",
                        "fuel_type": "gasoline",
                        "price_usd": round(float(gas_p), 4),
                        "price_loc": round(float(gas_p) * fx, 2),
                        "currency":  currency,
                        "fx_rate":   fx,
                        "source":    src_lbl,
                        "src_code":  src,
                        "collected": now.isoformat(),
                        "updated":   now.isoformat(),
                        "status":    "verified" if src != "E" else "estimated",
                    })
                    existing_keys.add(gas_key)
                    added += 1

            # Diesel
            die_key = f"{name}|{date_str}|diesel"
            if die_key not in existing_keys and week_idx < len(die_series):
                die_p = die_series[week_idx]
                if die_p is not None:
                    db["entries"].append({
                        "key":       die_key,
                        "country":   name,
                        "date":      date_str,
                        "week":      f"W{week_idx+1:02d}",
                        "fuel_type": "diesel",
                        "price_usd": round(float(die_p), 4),
                        "price_loc": round(float(die_p) * fx, 2),
                        "currency":  currency,
                        "fx_rate":   fx,
                        "source":    src_lbl,
                        "src_code":  src,
                        "collected": now.isoformat(),
                        "updated":   now.isoformat(),
                        "status":    "verified" if src != "E" else "estimated",
                    })
                    existing_keys.add(die_key)
                    added += 1

            # LPG (dernière semaine seulement)
            if week_idx == len(D.WEEK_DATES) - 1:
                lpg_key = f"{name}|{date_str}|lpg"
                if lpg_key not in existing_keys:
                    db["entries"].append({
                        "key":       lpg_key,
                        "country":   name,
                        "date":      date_str,
                        "week":      f"W{week_idx+1:02d}",
                        "fuel_type": "lpg",
                        "price_usd": round(float(lpg_price), 4),
                        "price_loc": round(float(lpg_price) * fx, 2),
                        "currency":  currency,
                        "fx_rate":   fx,
                        "source":    src_lbl,
                        "src_code":  src,
                        "collected": now.isoformat(),
                        "updated":   now.isoformat(),
                        "status":    "verified" if src != "E" else "estimated",
                    })
                    existing_keys.add(lpg_key)
                    added += 1

    db["last_run"]      = now.isoformat()
    db["populated_at"]  = now.isoformat()
    db["n_countries"]   = 54
    db["n_weeks"]       = D.N_WEEKS
    db["week_labels"]   = D.WEEK_LABELS
    db["period_start"]  = D.PERIOD_START.isoformat()
    db["period_end"]    = D.PERIOD_END.isoformat()

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    # Rapport
    countries_gas = len(set(
        e["country"] for e in db["entries"] if e["fuel_type"] == "gasoline"
    ))
    verified = sum(1 for e in db["entries"] if e.get("status") == "verified")
    estimated = sum(1 for e in db["entries"] if e.get("status") == "estimated")

    print(f"\n{'='*60}")
    print(f"  DB POPULATED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"  Entrées ajoutées   : {added}")
    print(f"  Total DB           : {len(db['entries'])}")
    print(f"  Pays avec données  : {countries_gas}/54")
    print(f"  Vérifiées (A/B/C/D): {verified}")
    print(f"  Estimées (E)       : {estimated}")
    print(f"  Période            : {D.WEEK_LABELS[0]} → {D.WEEK_LABELS[-1]}")
    print(f"  Fichier            : {DB_FILE}")
    print(f"{'='*60}")

    # Répartition par source
    from collections import Counter
    src_counts = Counter(
        e["src_code"] for e in db["entries"] if e["fuel_type"] == "gasoline"
    )
    print(f"\n  Répartition sources (essence):")
    for src_code in ["D","C","B","A","E"]:
        n = src_counts.get(src_code, 0)
        label = SOURCE_LABELS.get(src_code,"?")[:45]
        bar = "█" * min(20, n//5)
        print(f"    {src_code}: {n:>4} pts  {bar}  {label}")

    return db


if __name__ == "__main__":
    db = populate()

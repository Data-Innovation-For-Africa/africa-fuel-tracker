"""
collector.py — Africa Fuel Tracker · Real Data Collector
=========================================================
Utilise Playwright (navigateur headless) pour scraper GPP.
Playwright simule un vrai navigateur Chrome → contourne JS et Cloudflare.

Pipeline:
  1. Playwright scrape GPP Africa table    → prix actuels 54 pays
  2. Playwright scrape GPP par pays        → historique hebdo Jan–Mar 2026
  3. Sauvegarde dans data/prices_db.json
  4. build_records_from_db() → records pour Excel + Dashboard
"""

import json, re, datetime
from pathlib import Path

HERE     = Path(__file__).parent
DATA_DIR = HERE.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_FILE  = DATA_DIR / "prices_db.json"


# ── Slugs GPP pour chaque pays africain ──────────────────────────────────────
GPP_SLUGS = {
    "Algeria":           "Algeria",
    "Angola":            "Angola",
    "Benin":             "Benin",
    "Botswana":          "Botswana",
    "Burkina Faso":      "Burkina-Faso",
    "Burundi":           "Burundi",
    "Cabo Verde":        "Cape-Verde",
    "Cameroon":          "Cameroon",
    "CAR":               "Central-African-Republic",
    "Chad":              "Chad",
    "Comoros":           "Comoros",
    "Congo DR":          "Congo",
    "Congo Rep.":        "Republic-of-the-Congo",
    "Djibouti":          "Djibouti",
    "Egypt":             "Egypt",
    "Equatorial Guinea": "Equatorial-Guinea",
    "Eritrea":           "Eritrea",
    "Eswatini":          "Swaziland",
    "Ethiopia":          "Ethiopia",
    "Gabon":             "Gabon",
    "Gambia":            "Gambia",
    "Ghana":             "Ghana",
    "Guinea":            "Guinea",
    "Guinea-Bissau":     "Guinea-Bissau",
    "Ivory Coast":       "Ivory-Coast",
    "Kenya":             "Kenya",
    "Lesotho":           "Lesotho",
    "Liberia":           "Liberia",
    "Libya":             "Libya",
    "Madagascar":        "Madagascar",
    "Malawi":            "Malawi",
    "Mali":              "Mali",
    "Mauritania":        "Mauritania",
    "Mauritius":         "Mauritius",
    "Morocco":           "Morocco",
    "Mozambique":        "Mozambique",
    "Namibia":           "Namibia",
    "Niger":             "Niger",
    "Nigeria":           "Nigeria",
    "Rwanda":            "Rwanda",
    "Sao Tome":          "Sao-Tome-And-Principe",
    "Senegal":           "Senegal",
    "Seychelles":        "Seychelles",
    "Sierra Leone":      "Sierra-Leone",
    "Somalia":           "Somalia",
    "South Africa":      "South-Africa",
    "South Sudan":       "South-Sudan",
    "Sudan":             "Sudan",
    "Tanzania":          "Tanzania",
    "Togo":              "Togo",
    "Tunisia":           "Tunisia",
    "Uganda":            "Uganda",
    "Zambia":            "Zambia",
    "Zimbabwe":          "Zimbabwe",
}

# Correspondance noms GPP → noms internes
GPP_NAME_MAP = {
    "South Africa":"South Africa","Nigeria":"Nigeria","Kenya":"Kenya",
    "Egypt":"Egypt","Ethiopia":"Ethiopia","Ghana":"Ghana",
    "Tanzania":"Tanzania","Uganda":"Uganda","Mozambique":"Mozambique",
    "Zambia":"Zambia","Zimbabwe":"Zimbabwe","Senegal":"Senegal",
    "Ivory Coast":"Ivory Coast","Cameroon":"Cameroon","Angola":"Angola",
    "Algeria":"Algeria","Morocco":"Morocco","Tunisia":"Tunisia",
    "Libya":"Libya","Sudan":"Sudan","Rwanda":"Rwanda",
    "Malawi":"Malawi","Madagascar":"Madagascar","Mali":"Mali",
    "Burkina Faso":"Burkina Faso","Benin":"Benin","Togo":"Togo",
    "Niger":"Niger","Guinea":"Guinea","Sierra Leone":"Sierra Leone",
    "Liberia":"Liberia","Gambia":"Gambia","Botswana":"Botswana",
    "Namibia":"Namibia","Eswatini":"Eswatini","Lesotho":"Lesotho",
    "Mauritius":"Mauritius","Seychelles":"Seychelles","Comoros":"Comoros",
    "Djibouti":"Djibouti","Eritrea":"Eritrea","Somalia":"Somalia",
    "South Sudan":"South Sudan","Burundi":"Burundi","Chad":"Chad",
    "Gabon":"Gabon","Equatorial Guinea":"Equatorial Guinea",
    "Cabo Verde":"Cabo Verde","Central African Republic":"CAR",
    "Congo":"Congo DR","Republic of the Congo":"Congo Rep.",
    "Guinea-Bissau":"Guinea-Bissau","Mauritania":"Mauritania",
    "Sao Tome And Principe":"Sao Tome",
}


# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES PERSISTANTE
# ══════════════════════════════════════════════════════════════════════════════

def load_db():
    if DB_FILE.exists():
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"version": 2, "entries": [], "last_run": None}


def save_db(db):
    db["last_run"] = datetime.datetime.utcnow().isoformat()
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    print(f"   💾  DB saved → {DB_FILE}  ({len(db['entries'])} entries)")


def upsert(db, country, date_str, fuel_type, price_usd, source, currency, fx):
    key = f"{country}|{date_str}|{fuel_type}"
    for e in db["entries"]:
        if e.get("key") == key:
            e.update({
                "price_usd": price_usd,
                "price_loc": round(price_usd * fx, 2),
                "source": source,
                "updated": datetime.datetime.utcnow().isoformat(),
                "status": "live",
            })
            return
    db["entries"].append({
        "key": key, "country": country, "date": date_str,
        "fuel_type": fuel_type, "price_usd": price_usd,
        "price_loc": round(price_usd * fx, 2), "currency": currency,
        "fx_rate": fx, "source": source,
        "collected": datetime.datetime.utcnow().isoformat(),
        "updated": datetime.datetime.utcnow().isoformat(),
        "status": "live",
    })


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATEUR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def run_collection():
    from data import FX_RATES, COUNTRIES
    from scraper_playwright import run_playwright_scraper

    today  = datetime.date.today().isoformat()
    db     = load_db()
    stats  = {"live": 0, "history": 0, "failed": 0}

    print(f"\n{'='*60}")
    print(f"  AFRICA FUEL TRACKER — REAL DATA COLLECTION (Playwright)")
    print(f"  {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    # ── Scraping Playwright ────────────────────────────────────────────────
    print("STEP 1 — Scraping GPP via Playwright (navigateur headless)")
    scraped = run_playwright_scraper(GPP_SLUGS)

    if not scraped:
        print("  ❌ Playwright n'a rien retourné — fallback seed")
        save_db(db)
        return db

    country_defs = {c[0]: c for c in COUNTRIES}

    # ── Stocke les prix actuels ────────────────────────────────────────────
    print("\nSTEP 2 — Stockage des prix actuels")
    for gpp_name, our_name in GPP_NAME_MAP.items():
        if our_name not in country_defs or gpp_name not in scraped:
            continue
        _, _, currency, _ = country_defs[our_name]
        fx = FX_RATES.get(currency, 1.0)
        info = scraped[gpp_name]

        if info.get("current_gas"):
            upsert(db, our_name, today, "gasoline",
                   info["current_gas"], "GlobalPetrolPrices.com", currency, fx)
            stats["live"] += 1
        if info.get("current_die"):
            upsert(db, our_name, today, "diesel",
                   info["current_die"], "GlobalPetrolPrices.com", currency, fx)

    print(f"  → {stats['live']} prix actuels stockés")

    # ── Stocke l'historique Jan–Mar 2026 ──────────────────────────────────
    print("\nSTEP 3 — Stockage historique hebdomadaire Jan–Mar 2026")
    for country_name, info in scraped.items():
        # Résoud le nom GPP → nom interne
        our_name = GPP_NAME_MAP.get(country_name, country_name)
        if our_name not in country_defs:
            continue
        _, _, currency, _ = country_defs[our_name]
        fx = FX_RATES.get(currency, 1.0)
        gpp_url = f"https://www.globalpetrolprices.com/{GPP_SLUGS.get(our_name, '')}/gasoline_prices/"

        for fuel_type, key in [("gasoline", "history_gas"), ("diesel", "history_die")]:
            for pt in info.get(key, []):
                upsert(db, our_name, pt["date"], fuel_type,
                       pt["price_usd"], gpp_url, currency, fx)
                stats["history"] += 1

    print(f"  → {stats['history']} points historiques stockés")

    # ── Sauvegarde ────────────────────────────────────────────────────────
    print("\nSTEP 4 — Saving database")
    save_db(db)

    countries_ok = len(set(e["country"] for e in db["entries"]))
    print(f"\n{'='*60}")
    print(f"  COLLECTION COMPLETE")
    print(f"  Prix actuels       : {stats['live']}")
    print(f"  Points historiques : {stats['history']}")
    print(f"  Pays avec données  : {countries_ok}/54")
    print(f"  Total DB           : {len(db['entries'])} entrées")
    print(f"{'='*60}\n")
    return db


# ══════════════════════════════════════════════════════════════════════════════
# DB → records pour le pipeline (Excel + Dashboard)
# ══════════════════════════════════════════════════════════════════════════════

def build_records_from_db(fx_rates=None):
    from data import COUNTRIES, FX_RATES, WEEK_DATES, N_WEEKS, build_records

    if fx_rates is None:
        fx_rates = FX_RATES

    db = load_db()
    if not db["entries"]:
        print("   ⚠️  DB vide — utilisation des données seed calibrées")
        return build_records(fx_rates)

    seed_recs = {r["name"]: r for r in build_records(fx_rates)}
    now       = datetime.datetime.utcnow()
    records   = []

    for name, region, currency, octane in COUNTRIES:
        fx   = fx_rates.get(currency, 1.0)
        seed = seed_recs.get(name, {})

        def best_price(fuel_type, week_date):
            ds = week_date.isoformat()
            # Correspondance exacte
            exact = [e for e in db["entries"]
                     if e["country"] == name
                     and e["fuel_type"] == fuel_type
                     and e["date"] == ds]
            if exact:
                return exact[0]["price_usd"], "live"
            # Plus proche ±7 jours
            candidates = [e for e in db["entries"]
                          if e["country"] == name and e["fuel_type"] == fuel_type]
            if candidates:
                near = min(candidates, key=lambda e: abs(
                    (datetime.date.fromisoformat(e["date"]) - week_date).days))
                gap  = abs((datetime.date.fromisoformat(near["date"]) - week_date).days)
                if gap <= 7:
                    return near["price_usd"], "interpolated"
            # Fallback seed
            wi  = WEEK_DATES.index(week_date) if week_date in WEEK_DATES else -1
            sw  = seed.get("gas_usd_w" if fuel_type == "gasoline" else "die_usd_w", [])
            return (sw[wi] if 0 <= wi < len(sw) else 1.0), "seed"

        gas_usd, die_usd, gas_status = [], [], []
        for wd in WEEK_DATES:
            gp, gs = best_price("gasoline", wd)
            dp, _  = best_price("diesel",   wd)
            gas_usd.append(round(float(gp), 4))
            die_usd.append(round(float(dp), 4))
            gas_status.append(gs)

        gas_loc = [round(p * fx, 2) for p in gas_usd]
        die_loc = [round(p * fx, 2) for p in die_usd]
        lpg_usd = seed.get("lpg_usd", 1.2)

        live_n  = gas_status.count("live") + gas_status.count("interpolated")
        quality = "live" if live_n >= 8 else ("partial" if live_n >= 3 else "seed")

        records.append({
            "name":      name, "region": region,
            "currency":  currency, "octane": octane, "fx_rate": fx,
            "gas_usd":   gas_usd[-1], "die_usd": die_usd[-1],
            "lpg_usd":   lpg_usd,
            "gas_loc":   gas_loc[-1], "die_loc": die_loc[-1],
            "lpg_loc":   round(lpg_usd * fx, 2),
            "gas_usd_w": gas_usd, "die_usd_w": die_usd,
            "gas_loc_w": gas_loc, "die_loc_w": die_loc,
            "chg_gas":   round((gas_usd[-1]-gas_usd[0])/gas_usd[0]*100, 2) if gas_usd[0] else 0,
            "chg_die":   round((die_usd[-1]-die_usd[0])/die_usd[0]*100, 2) if die_usd[0] else 0,
            "min_gas":   round(min(gas_usd), 4),
            "max_gas":   round(max(gas_usd), 4),
            "avg_gas":   round(sum(gas_usd) / len(gas_usd), 4),
            "data_quality": quality,
            "updated":   now.strftime("%Y-%m-%d %H:%M UTC"),
        })

    return sorted(records, key=lambda r: r["name"])


if __name__ == "__main__":
    run_collection()

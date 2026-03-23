"""
collector.py — Africa Fuel Tracker · Smart Data Collector
==========================================================
Pipeline de collecte en 3 étapes :

  ÉTAPE 1 — GPP (Playwright)
    Source principale : GlobalPetrolPrices.com
    Couverture        : 42 pays africains
    Données           : prix actuel + historique hebdo Jan→aujourd'hui
    URL pattern       : /{{slug}}/gasoline_prices/ + /diesel_prices/
    Fréquence         : Hebdomadaire (lundi GPP publie ses mises à jour)

  ÉTAPE 2 — Sources officielles nationales (Playwright/HTTP)
    5 pays clés (sources D) pour cross-validation :
    South Africa (FSIA), Egypt (EGPC), Kenya (EPRA),
    Nigeria (NNPC/press), Morocco (presse)

  ÉTAPE 3 — Fallback base data.py
    12 pays absents de GPP → données calibrées conservées
    Chad, Comoros, Congo Rep., Djibouti, Equatorial Guinea,
    Eritrea, Gambia, Guinea-Bissau, Mauritania, Sao Tome,
    Somalia, South Sudan
"""

import json, re, datetime, time, requests
from pathlib import Path

HERE     = Path(__file__).parent
DATA_DIR = HERE.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_FILE  = DATA_DIR / "prices_db.json"

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ══════════════════════════════════════════════════════════════════════════════
# DB
# ══════════════════════════════════════════════════════════════════════════════

def load_db():
    if DB_FILE.exists():
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"version": 3, "entries": []}


def save_db(db):
    db["last_run"] = datetime.datetime.utcnow().isoformat()
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    n = len(db["entries"])
    print(f"   💾 DB saved: {n} entries")


def upsert(db, country, date_str, fuel_type, price_usd, source, src_code, currency, fx, **extra):
    """
    Insert ou mise à jour d'un prix dans la DB.
    RÈGLE FONDAMENTALE : on n'écrase JAMAIS les données historiques.
      - Même clé (country|date|fuel) → garde la source de meilleure qualité
      - Nouvelle date → toujours ajoutée (append)
      - Prix local calculé avec le taux FX de la période (pas le taux actuel)
    """
    key   = f"{country}|{date_str}|{fuel_type}"
    ORDER = {"D":5, "C":4, "B":3, "A":2, "E":1}
    new_p = ORDER.get(src_code, 0)
    now   = datetime.datetime.utcnow().isoformat()

    # FX rate: use the one derived from GPP data if available
    # GPP gives both local and USD → exact period rate = local/usd
    fx_period = extra.pop("fx_period", fx)

    entry = {
        "key":       key,
        "country":   country,
        "date":      date_str,
        "fuel_type": fuel_type,
        "price_usd": round(float(price_usd), 4),
        "price_loc": round(float(price_usd) * fx_period, 2),
        "currency":  currency,
        "fx_rate":   round(fx_period, 4),   # period-specific FX rate
        "source":    source,
        "src_code":  src_code,
        "updated":   now,
        "status":    "live",
        **extra
    }

    for i, e in enumerate(db["entries"]):
        if e.get("key") == key:
            old_p = ORDER.get(e.get("src_code", "E"), 0)
            if new_p > old_p:
                # Better source → update price but KEEP collected date
                entry["collected"] = e.get("collected", now)
                db["entries"][i] = entry
            # Same or lower priority → keep existing, don't overwrite
            return

    # New entry → append
    entry["collected"] = now
    db["entries"].append(entry)


def run_gpp_collection(db, fx_rates, country_defs, period_to=None):
    """Scrape GPP pour les 42 pays africains et stocke dans DB."""
    try:
        from scraper_gpp import run_gpp_scraper, save_gpp_to_db
    except ImportError:
        print("  ⚠️  scraper_gpp.py not found")
        return 0

    if not period_to:
        period_to = datetime.date.today().isoformat()

    print(f"   Scraping {len(country_defs)} countries via Playwright...")
    gpp_results = run_gpp_scraper(period_to)

    if not gpp_results:
        print("   ⚠️  GPP scraper returned no data")
        return 0

    n = save_gpp_to_db(gpp_results, db, fx_rates, country_defs)
    return n


# ══════════════════════════════════════════════════════════════════════════════
# ÉTAPE 2 — Sources officielles nationales (HTTP simple)
# ══════════════════════════════════════════════════════════════════════════════

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})

def _get(url):
    try:
        r = SESSION.get(url, timeout=20, verify=False, allow_redirects=True)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"   ⚠️  {url[:55]}: {str(e)[:50]}")
        return None


def _sfloat(text):
    s = re.sub(r"[^\d.]", "", str(text or "").strip())
    try:
        v = float(s); return v if v > 0 else None
    except: return None


def scrape_fsia_south_africa():
    """FSIA — Fuels Industry Association SA (officiel, mensuel)."""
    r = _get("https://fuelsindustry.org.za/consumer-information/fuel-prices-current-past/")
    if not r: return {}
    # Pattern: 95 ULP (c/l) *1992,00 (example from search results)
    m = re.search(r'95\s*(?:ULP|LRP).*?\*?\s*(\d{4})[,.](\d{2})', r.text, re.I | re.S)
    if m:
        cents = int(m.group(1) + m.group(2)) / 100  # e.g. 1992.00 = R19.92
        from data import FX_RATES
        fx  = FX_RATES.get("ZAR", 18.55)
        usd = round(cents / fx, 4)
        print(f"   ✅ South Africa (FSIA): R{cents:.2f}/L = ${usd:.3f}/L")
        return {"price_usd": usd, "price_local": cents, "source": r.url, "src_code": "D"}
    return {}


def scrape_egypt_official():
    """BankLive/EGPC — Egypt official pump prices."""
    r = _get("https://banklive.net/en/petroleum-price")
    if not r: return {}
    from data import FX_RATES
    fx = FX_RATES.get("EGP", 50.2)
    m = re.search(r'(?:92|95|petrol|gasoline).*?(\d{2}(?:[.,]\d{1,2})?)\s*(?:EGP|ج)', r.text, re.I|re.S)
    if m:
        egp = _sfloat(m.group(1).replace(',','.'))
        if egp and 18 < egp < 35:
            usd = round(egp / fx, 4)
            print(f"   ✅ Egypt (BankLive): EGP{egp}/L = ${usd:.3f}/L")
            return {"price_usd": usd, "price_local": egp, "source": r.url, "src_code": "D"}
    return {}


def scrape_kenya_epra():
    """EPRA Kenya — Energy & Petroleum Regulatory Authority."""
    for url in ["https://www.epra.go.ke", "https://epra.go.ke"]:
        r = _get(url)
        if not r: continue
        m = re.search(r'(?:super|petrol|unleaded|95).*?(?:KSh|KES)\s*(\d{3}(?:[.,]\d{1,2})?)', r.text, re.I|re.S)
        if not m:
            m = re.search(r'(?:KSh|KES)\s*(\d{3}(?:[.,]\d{1,2})?)', r.text, re.I)
        if m:
            kes = _sfloat(m.group(1).replace(',','.'))
            if kes and 150 < kes < 250:
                from data import FX_RATES
                fx  = FX_RATES.get("KES", 130.5)
                usd = round(kes / fx, 4)
                print(f"   ✅ Kenya (EPRA): KSh{kes}/L = ${usd:.3f}/L")
                return {"price_usd": usd, "price_local": kes, "source": url, "src_code": "D"}
    return {}


def scrape_nigeria_press():
    """Nairametrics — prix pompe Nigeria."""
    r = _get("https://nairametrics.com/category/energy/")
    if not r: return {}
    from data import FX_RATES
    fx = FX_RATES.get("NGN", 1620)
    m = re.search(r'(?:petrol|PMS|fuel).*?(?:N|₦)\s*(\d{3,4}(?:[.,]\d{1,2})?)\s*(?:/[Ll]|per)', r.text, re.I|re.S)
    if not m:
        m = re.search(r'(?:N|₦)(\d{3,4})\s*(?:/litre|per litre|/L)', r.text, re.I)
    if m:
        ngn = _sfloat(m.group(1).replace(',','.'))
        if ngn and 700 < ngn < 2500:
            usd = round(ngn / fx, 4)
            print(f"   ✅ Nigeria (Nairametrics): N{ngn}/L = ${usd:.3f}/L")
            return {"price_usd": usd, "price_local": ngn, "source": r.url, "src_code": "C"}
    return {}


def run_official_sources(db, fx_rates, country_defs, today):
    """Scrape les sources officielles pour 5 pays clés."""
    scrapers = [
        ("South Africa", scrape_fsia_south_africa),
        ("Egypt",        scrape_egypt_official),
        ("Kenya",        scrape_kenya_epra),
        ("Nigeria",      scrape_nigeria_press),
    ]
    n = 0
    for country, fn in scrapers:
        print(f"   → {country}...")
        result = fn()
        if result and result.get("price_usd"):
            if country not in country_defs: continue
            _, _, currency, _ = country_defs[country]
            fx = fx_rates.get(currency, 1.0)
            upsert(db, country, today, "gasoline",
                   result["price_usd"], result["source"], result["src_code"],
                   currency, fx)
            n += 1
        time.sleep(0.5)
    return n


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATEUR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def run_collection():
    from data import COUNTRIES, FX_RATES

    today        = datetime.date.today().isoformat()
    db           = load_db()
    country_defs = {c[0]: c for c in COUNTRIES}

    print(f"\n{'='*62}")
    print(f"  AFRICA FUEL TRACKER — WEEKLY COLLECTION")
    print(f"  Date: {today}")
    print(f"  Sources: GPP (42 pays) + Officiels (5 pays)")
    print(f"{'='*62}\n")

    # ── Étape 1 : GPP ──────────────────────────────────────────────────────
    print("STEP 1 — GlobalPetrolPrices.com (Playwright headless)")
    print(f"  → 42 pays × gas + diesel × historique Jan→{today}")
    n1 = run_gpp_collection(db, FX_RATES, country_defs, today)
    print(f"  → {n1} entries saved/updated\n")

    # ── Étape 2 : Sources officielles ─────────────────────────────────────
    print("STEP 2 — Sources officielles nationales (D-coded)")
    n2 = run_official_sources(db, FX_RATES, country_defs, today)
    print(f"  → {n2}/4 official sources collected\n")

    # ── Save ───────────────────────────────────────────────────────────────
    save_db(db)

    # ── Rapport ───────────────────────────────────────────────────────────
    gas_entries  = [e for e in db["entries"] if e["fuel_type"]=="gasoline"]
    n_countries  = len(set(e["country"] for e in gas_entries))
    live_today   = [e for e in gas_entries if e["date"]==today and e.get("status")=="live"]
    from collections import Counter
    srcs = Counter(e.get("src_code","?") for e in gas_entries)

    print(f"{'='*62}")
    print(f"  COLLECTION COMPLETE")
    print(f"  Pays couverts      : {n_countries}/54")
    print(f"  Live aujourd'hui   : {len(live_today)} pays")
    print(f"  Total DB (essence) : {len(gas_entries)} points")
    print(f"  Sources: D={srcs.get('D',0)} C={srcs.get('C',0)} "
          f"B={srcs.get('B',0)} A={srcs.get('A',0)} E={srcs.get('E',0)}")
    print(f"{'='*62}\n")
    return db


# ══════════════════════════════════════════════════════════════════════════════
# BUILD RECORDS DEPUIS DB
# ══════════════════════════════════════════════════════════════════════════════

def build_records_from_db(fx_rates=None):
    """Construit les records pour Excel + Dashboard depuis la DB."""
    from data import COUNTRIES, FX_RATES, WEEK_DATES, N_WEEKS, build_records, LPG_USD

    if fx_rates is None:
        fx_rates = FX_RATES

    db = load_db()
    if not db.get("entries"):
        print("   ⚠️  DB vide — fallback data.py")
        return build_records(fx_rates)

    # Index: (country, date, fuel) → entry
    ORDER = {"D":5,"C":4,"B":3,"A":2,"E":1}
    idx = {}
    for e in db["entries"]:
        k = (e["country"], e["date"], e["fuel_type"])
        if k not in idx or ORDER.get(e.get("src_code","E"),0) > ORDER.get(idx[k].get("src_code","E"),0):
            idx[k] = e

    now     = datetime.datetime.utcnow()
    records = []

    for name, region, currency, octane in COUNTRIES:
        fx = fx_rates.get(currency, 1.0)

        gas_usd, die_usd, gas_srcs = [], [], []
        for wd in WEEK_DATES:
            ds  = wd.isoformat()
            ge  = idx.get((name, ds, "gasoline"))
            de  = idx.get((name, ds, "diesel"))

            # Gas
            if ge:
                gas_usd.append(round(float(ge["price_usd"]),4))
                gas_srcs.append(ge.get("src_code","A"))
            else:
                # Nearest available
                cands = [(e["date"], float(e["price_usd"]))
                         for e in db["entries"]
                         if e["country"]==name and e["fuel_type"]=="gasoline"]
                if cands:
                    near = min(cands, key=lambda x: abs((datetime.date.fromisoformat(x[0])-wd).days))
                    gas_usd.append(round(near[1],4))
                    gas_srcs.append("interp")
                else:
                    gas_usd.append(1.0)
                    gas_srcs.append("missing")

            # Diesel
            if de:
                die_usd.append(round(float(de["price_usd"]),4))
            else:
                cands_d = [(e["date"], float(e["price_usd"]))
                           for e in db["entries"]
                           if e["country"]==name and e["fuel_type"]=="diesel"]
                if cands_d:
                    near = min(cands_d, key=lambda x: abs((datetime.date.fromisoformat(x[0])-wd).days))
                    die_usd.append(round(near[1],4))
                else:
                    die_usd.append(round(gas_usd[-1]*0.9,4))

        gas_loc = [round(p*fx,2) for p in gas_usd]
        die_loc = [round(p*fx,2) for p in die_usd]

        lpg_e   = idx.get((name, WEEK_DATES[-1].isoformat(), "lpg"))
        lpg_usd = float(lpg_e["price_usd"]) if lpg_e else LPG_USD.get(name,1.2)

        real_srcs = [s for s in gas_srcs if s not in ("missing","interp")]
        quality   = "live" if any(s in ("D","C","B","A") for s in gas_srcs[-3:]) else \
                    "verified" if real_srcs else "estimated"

        records.append({
            "name":         name,  "region":   region,
            "currency":     currency, "octane": octane, "fx_rate": fx,
            "gas_usd":      gas_usd[-1], "die_usd": die_usd[-1],
            "lpg_usd":      round(lpg_usd,4),
            "gas_loc":      gas_loc[-1], "die_loc": die_loc[-1],
            "lpg_loc":      round(lpg_usd*fx,2),
            "gas_usd_w":    gas_usd,   "die_usd_w": die_usd,
            "gas_loc_w":    gas_loc,   "die_loc_w": die_loc,
            "chg_gas":      round((gas_usd[-1]-gas_usd[0])/gas_usd[0]*100,2) if gas_usd[0] else 0,
            "chg_die":      round((die_usd[-1]-die_usd[0])/die_usd[0]*100,2) if die_usd[0] else 0,
            "min_gas":      round(min(gas_usd),4),
            "max_gas":      round(max(gas_usd),4),
            "avg_gas":      round(sum(gas_usd)/len(gas_usd),4),
            "data_quality": quality,
            "updated":      now.strftime("%Y-%m-%d %H:%M UTC"),
        })

    return sorted(records, key=lambda r: r["name"])


if __name__ == "__main__":
    run_collection()

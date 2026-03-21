"""
collector.py — Africa Fuel Tracker · Real Data Collector
=========================================================
Methodology (10 steps, inspired by manual research approach):

STEP 1 — RhinoCarHire.com/World-Fuel-Prices/Africa.aspx
          39 countries · Petrol + Diesel EUR → USD (current week)

STEP 2 — GlobalPetrolPrices.com Africa snapshot
          Via web search for cached/indexed pages + direct fetch

STEP 3 — Press articles (Zawya, Nigerian Tribune, Tuko, Nairametrics)
          Quote GPP data directly — accessible without JS

STEP 4 — TradingEconomics (aggregates GPP monthly)
          Cross-validation of GPP monthly values

STEP 5 — Official national sources (SA DMRE, EPRA Kenya, NNPC, BankLive Egypt)
          D-coded sources = highest reliability

STEP 6 — Update prices_db.json with all collected data
          Each entry stamped with source code A/B/C/D

STEP 7 — build_records_from_db() merges DB with base data.py values
"""

import requests, re, json, datetime, time
from pathlib import Path
from bs4 import BeautifulSoup

HERE     = Path(__file__).parent
DATA_DIR = HERE.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_FILE  = DATA_DIR / "prices_db.json"

# EUR/USD monthly rates (updated manually each month)
EUR_USD = {
    "2026-01": 1.033,
    "2026-02": 1.040,
    "2026-03": 1.085,
}

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.google.com/",
})
TIMEOUT = 20

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def _get(url, verify=True):
    for attempt in range(2):
        try:
            r = SESSION.get(url, timeout=TIMEOUT, verify=verify, allow_redirects=True)
            r.raise_for_status()
            return r
        except requests.exceptions.SSLError:
            if verify:
                return _get(url, verify=False)
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
            else:
                print(f"   ⚠️  {url[:60]}: {type(e).__name__}: {str(e)[:60]}")
    return None


def _safe_float(text):
    if not text:
        return None
    s = re.sub(r"[^\d.]", "", str(text).strip())
    try:
        v = float(s)
        return v if v > 0 else None
    except (ValueError, TypeError):
        return None


def _eur_to_usd(eur_price, month_key="2026-03"):
    rate = EUR_USD.get(month_key, 1.085)
    return round(eur_price * rate, 4)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — RhinoCarHire.com (39 African countries, EUR prices)
# Most reliable single source: table format, no JS protection
# ══════════════════════════════════════════════════════════════════════════════

RHINO_NAME_MAP = {
    "Algeria":"Algeria","Angola":"Angola","Botswana":"Botswana",
    "Burkina Faso":"Burkina Faso","Burundi":"Burundi","Cameroon":"Cameroon",
    "Cape Verde":"Cabo Verde","Chad":"Chad","Congo":"Congo DR",
    "Côte d'Ivoire":"Ivory Coast","Djibouti":"Djibouti","Egypt":"Egypt",
    "Eritrea":"Eritrea","Ethiopia":"Ethiopia","Gabon":"Gabon",
    "Gambia":"Gambia","Ghana":"Ghana","Guinea":"Guinea","Kenya":"Kenya",
    "Lesotho":"Lesotho","Liberia":"Liberia","Libya":"Libya",
    "Madagascar":"Madagascar","Malawi":"Malawi","Mali":"Mali",
    "Mauritania":"Mauritania","Mauritius":"Mauritius","Morocco":"Morocco",
    "Mozambique":"Mozambique","Namibia":"Namibia","Niger":"Niger",
    "Nigeria":"Nigeria","Rwanda":"Rwanda","Senegal":"Senegal",
    "Sierra Leone":"Sierra Leone","South Africa":"South Africa",
    "Sudan":"Sudan","Tanzania":"Tanzania","Togo":"Togo",
    "Tunisia":"Tunisia","Uganda":"Uganda","Zambia":"Zambia",
    "Zimbabwe":"Zimbabwe","South Sudan":"South Sudan",
    "Central African Republic":"CAR","Sao Tome and Principe":"Sao Tome",
    "Equatorial Guinea":"Equatorial Guinea","Seychelles":"Seychelles",
    "Somalia":"Somalia","Benin":"Benin","Eswatini":"Eswatini",
    "Guinea-Bissau":"Guinea-Bissau","Comoros":"Comoros",
    "Republic of the Congo":"Congo Rep.",
}

def scrape_rhinocarhire():
    """
    Scrape https://rhinocarhire.com/World-Fuel-Prices/Africa.aspx
    Returns {country_name: {"gas_eur": float, "die_eur": float, "gas_usd": float, "die_usd": float}}
    """
    url   = "https://rhinocarhire.com/World-Fuel-Prices/Africa.aspx"
    today = datetime.date.today()
    month_key = today.strftime("%Y-%m")
    rate  = EUR_USD.get(month_key, EUR_USD.get("2026-03", 1.085))

    print(f"   Fetching RhinoCarHire ({url}) ...")
    r = _get(url)
    if not r:
        print("   ⚠️  RhinoCarHire: failed to fetch")
        return {}

    soup    = BeautifulSoup(r.text, "lxml")
    results = {}

    # RhinoCarHire table structure:
    # <table> <tr> <td>Country</td> <td>€/L petrol</td> <td>€/L diesel</td> ... </tr>
    tables = soup.find_all("table")
    for table in tables:
        for row in table.find_all("tr"):
            cols = row.find_all(["td","th"])
            if len(cols) < 3:
                continue
            name_raw = cols[0].get_text(strip=True)
            # Map to internal name
            our_name = RHINO_NAME_MAP.get(name_raw)
            if not our_name:
                # Fuzzy match
                for rhino_n, int_n in RHINO_NAME_MAP.items():
                    if rhino_n.lower() in name_raw.lower() or name_raw.lower() in rhino_n.lower():
                        our_name = int_n
                        break
            if not our_name:
                continue

            # Try to find EUR prices in columns
            prices = []
            for col in cols[1:]:
                v = _safe_float(col.get_text(strip=True))
                if v and 0.1 < v < 5:  # EUR/L range
                    prices.append(v)

            if len(prices) >= 1:
                gas_eur = prices[0]
                die_eur = prices[1] if len(prices) >= 2 else None
                results[our_name] = {
                    "gas_eur": gas_eur,
                    "die_eur": die_eur,
                    "gas_usd": _eur_to_usd(gas_eur, month_key),
                    "die_usd": _eur_to_usd(die_eur, month_key) if die_eur else None,
                    "source":  "RhinoCarHire",
                    "src_code":"B",
                    "date":    today.isoformat(),
                }

    print(f"   ✅ RhinoCarHire: {len(results)} countries")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2+3 — Press articles that cite GPP data
# These are HTML pages (no JS protection) that quote GPP Africa rankings
# ══════════════════════════════════════════════════════════════════════════════

PRESS_SEARCHES = [
    # Zawya regularly publishes GPP Africa top 10 / bottom 10
    "https://www.zawya.com/en/economy/regional/",
    # Nairametrics publishes Nigerian fuel prices
    "https://nairametrics.com/2026/",
    # TradingEconomics Africa gasoline
    "https://tradingeconomics.com/country-list/gasoline-prices?continent=africa",
]

def scrape_tradingeconomics():
    """
    TradingEconomics aggregates GPP monthly data in a table.
    Returns {country: {"gas_usd": float}}
    """
    url = "https://tradingeconomics.com/country-list/gasoline-prices?continent=africa"
    print(f"   Fetching TradingEconomics ...")
    r = _get(url)
    if not r:
        return {}

    soup    = BeautifulSoup(r.text, "lxml")
    results = {}

    TE_NAME_MAP = {
        "South Africa":"South Africa","Nigeria":"Nigeria","Kenya":"Kenya",
        "Egypt":"Egypt","Ethiopia":"Ethiopia","Ghana":"Ghana",
        "Morocco":"Morocco","Tanzania":"Tanzania","Algeria":"Algeria",
        "Libya":"Libya","Sudan":"Sudan","Tunisia":"Tunisia",
        "Angola":"Angola","Cameroon":"Cameroon","Ivory Coast":"Ivory Coast",
        "Cote D'Ivoire":"Ivory Coast","Senegal":"Senegal","Uganda":"Uganda",
        "Zambia":"Zambia","Zimbabwe":"Zimbabwe","Mali":"Mali",
        "Burkina Faso":"Burkina Faso","Rwanda":"Rwanda","Malawi":"Malawi",
        "Mozambique":"Mozambique","Madagascar":"Madagascar",
        "Botswana":"Botswana","Namibia":"Namibia","Mauritius":"Mauritius",
        "Cape Verde":"Cabo Verde","Cape-Verde":"Cabo Verde",
        "Seychelles":"Seychelles","Sierra Leone":"Sierra Leone",
        "Lesotho":"Lesotho","Liberia":"Liberia","Guinea":"Guinea",
        "Togo":"Togo","Benin":"Benin","Gabon":"Gabon",
        "Congo":"Congo DR","Burundi":"Burundi","Eritrea":"Eritrea",
    }

    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        name_raw = cols[0].get_text(strip=True)
        our_name = TE_NAME_MAP.get(name_raw)
        if not our_name:
            continue
        # Price in USD/L
        for col in cols[1:]:
            v = _safe_float(col.get_text(strip=True))
            if v and 0.01 < v < 5:
                results[our_name] = {
                    "gas_usd": v,
                    "source":  "TradingEconomics (GPP)",
                    "src_code":"A",
                    "date":    datetime.date.today().isoformat(),
                }
                break

    print(f"   ✅ TradingEconomics: {len(results)} countries")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Official national sources (D-coded, highest reliability)
# ══════════════════════════════════════════════════════════════════════════════

def scrape_sa_official():
    """South Africa DMRE official fuel price (ZAR/L → USD)."""
    from data import FX_RATES
    urls = [
        "https://www.energy.gov.za/files/esources/petroleum/petroleum_arch.htm",
        "https://www.dmre.gov.za/media/press-releases",
        "https://www.energy.gov.za",
    ]
    for url in urls:
        r = _get(url, verify=False)
        if not r: continue
        text = r.text
        # South Africa coastal 95 ULP ~R22-26/L
        m = re.search(r'(?:95\s+ULP|Petrol\s+95|coastal).*?R?\s*(\d{2}[\.,]\d{1,3})\s*/?\s*[Ll]', text, re.I | re.S)
        if m:
            zar = _safe_float(m.group(1))
            if zar and 20 < zar < 35:
                usd = round(zar / FX_RATES["ZAR"], 4)
                print(f"   ✅ South Africa (official): R{zar}/L = ${usd:.3f}/L")
                return {"gas_usd": usd, "gas_zar": zar, "source": url, "src_code": "D"}
    # Try a simpler search for ZAR values
    for url in urls:
        r = _get(url, verify=False)
        if not r: continue
        zar_vals = re.findall(r'\b(\d{2}\.\d{2})\b', r.text)
        for z in zar_vals:
            v = _safe_float(z)
            if v and 21 < v < 30:
                usd = round(v / FX_RATES["ZAR"], 4)
                return {"gas_usd": usd, "gas_zar": v, "source": url, "src_code": "D"}
    return {}


def scrape_egypt_official():
    """Egypt petroleum prices from BankLive or official portal."""
    from data import FX_RATES
    urls = [
        "https://banklive.net/en/petroleum-price",
        "https://www.egpc.com.eg/en/prices",
    ]
    for url in urls:
        r = _get(url, verify=False)
        if not r: continue
        text = r.text
        # 92 octane EGP/L ~21-24 EGP
        m = re.search(r'(?:92|petrol|gasoline).*?(\d{2}(?:\.\d{1,2})?)\s*(?:EGP|L|litre)', text, re.I | re.S)
        if m:
            egp = _safe_float(m.group(1))
            if egp and 18 < egp < 30:
                usd = round(egp / FX_RATES["EGP"], 4)
                print(f"   ✅ Egypt (official): EGP{egp}/L = ${usd:.3f}/L")
                return {"gas_usd": usd, "gas_egp": egp, "source": url, "src_code": "D"}
    return {}


def scrape_kenya_official():
    """Kenya EPRA maximum pump prices."""
    from data import FX_RATES
    urls = [
        "https://www.epra.go.ke",
        "https://epra.go.ke/petroleum/petroleum-prices/",
        "https://www.epra.go.ke/download-category/petroleum-prices/",
    ]
    for url in urls:
        r = _get(url, verify=False)
        if not r: continue
        text = r.text
        # Nairobi super petrol ~KSh 165-185/L
        m = re.search(r'(?:super|petrol|unleaded).*?(?:KSh|KES|Ksh)\s*(\d{3}(?:\.\d{1,2})?)', text, re.I | re.S)
        if not m:
            m = re.search(r'(?:KSh|KES|Ksh)\s*(\d{3}(?:\.\d{1,2})?)', text, re.I)
        if m:
            kes = _safe_float(m.group(1))
            if kes and 150 < kes < 220:
                usd = round(kes / FX_RATES["KES"], 4)
                print(f"   ✅ Kenya (EPRA): KSh{kes}/L = ${usd:.3f}/L")
                return {"gas_usd": usd, "gas_kes": kes, "source": url, "src_code": "D"}
    return {}


def scrape_nigeria_official():
    """Nigeria NNPC / press for current pump price."""
    from data import FX_RATES
    urls = [
        "https://nnpcgroup.com",
        "https://nairametrics.com/category/energy/",
        "https://punchng.com/tag/petrol-price/",
    ]
    for url in urls:
        r = _get(url, verify=False)
        if not r: continue
        text = r.text
        # Nigeria NGN/L ~850-1300
        m = re.search(r'(?:petrol|PMS|fuel).*?(?:N|NGN|₦)\s*(\d{3,4}(?:\.\d{1,2})?)\s*/?\s*[Ll]', text, re.I | re.S)
        if not m:
            m = re.search(r'(?:N|₦)(\d{3,4})\s*(?:/litre|per litre|/L)', text, re.I)
        if m:
            ngn = _safe_float(m.group(1))
            if ngn and 700 < ngn < 2000:
                usd = round(ngn / FX_RATES["NGN"], 4)
                print(f"   ✅ Nigeria (official): N{ngn}/L = ${usd:.3f}/L")
                return {"gas_usd": usd, "gas_ngn": ngn, "source": url, "src_code": "C"}
    return {}


def scrape_morocco_official():
    """Morocco press for fuel prices (liberalized market)."""
    from data import FX_RATES
    urls = [
        "https://www.anre.ma",
        "https://en.le7tv.ma",
        "https://www.moroccoworldnews.com",
    ]
    for url in urls:
        r = _get(url, verify=False)
        if not r: continue
        text = r.text
        # Morocco MAD/L ~12-16
        m = re.search(r'(?:essence|petrol|gasoline|sans-plomb).*?(\d{2}(?:[.,]\d{1,2})?)\s*(?:DH|MAD|dirham)', text, re.I | re.S)
        if m:
            mad = _safe_float(m.group(1).replace(',', '.'))
            if mad and 10 < mad < 20:
                usd = round(mad / FX_RATES["MAD"], 4)
                print(f"   ✅ Morocco: MAD{mad}/L = ${usd:.3f}/L")
                return {"gas_usd": usd, "gas_mad": mad, "source": url, "src_code": "C"}
    return {}


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════════════

def load_db():
    if DB_FILE.exists():
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"version": 3, "entries": [], "last_run": None}


def save_db(db):
    db["last_run"] = datetime.datetime.utcnow().isoformat()
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    print(f"   💾  DB saved → {len(db['entries'])} entries")


def upsert(db, country, date_str, fuel_type, price_usd, source, src_code, currency, fx):
    key = f"{country}|{date_str}|{fuel_type}"
    entry = {
        "key": key, "country": country, "date": date_str,
        "fuel_type": fuel_type, "price_usd": price_usd,
        "price_loc": round(price_usd * fx, 2), "currency": currency,
        "fx_rate": fx, "source": source, "src_code": src_code,
        "updated": datetime.datetime.utcnow().isoformat(), "status": "live",
    }
    for i, e in enumerate(db["entries"]):
        if e.get("key") == key:
            # Only update if new src_code is better (D > C > B > A)
            order = {"D": 4, "C": 3, "B": 2, "A": 1}
            if order.get(src_code, 0) >= order.get(e.get("src_code", "A"), 1):
                db["entries"][i] = {**e, **entry}
            return
    db["entries"].append({**entry, "collected": datetime.datetime.utcnow().isoformat()})


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

def run_collection():
    from data import COUNTRIES, FX_RATES

    today   = datetime.date.today().isoformat()
    db      = load_db()
    stats   = {"live": 0, "official": 0, "failed": 0}
    country_defs = {c[0]: c for c in COUNTRIES}

    print(f"\n{'='*62}")
    print(f"  AFRICA FUEL TRACKER — REAL DATA COLLECTION")
    print(f"  {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Based on 10-step methodology (RhinoCarHire + GPP + Press + Official)")
    print(f"{'='*62}\n")

    def store(country, fuel_type, price_usd, source, src_code):
        if country not in country_defs or not price_usd:
            return False
        _, _, currency, _ = country_defs[country]
        fx = FX_RATES.get(currency, 1.0)
        upsert(db, country, today, fuel_type, price_usd, source, src_code, currency, fx)
        return True

    # ── Step 1: RhinoCarHire ──────────────────────────────────────────────
    print("STEP 1 — RhinoCarHire.com (EUR prices → USD)")
    rhino = scrape_rhinocarhire()
    for country, data in rhino.items():
        if store(country, "gasoline", data.get("gas_usd"), data["source"], "B"):
            stats["live"] += 1
        if data.get("die_usd"):
            store(country, "diesel", data["die_usd"], data["source"], "B")
    time.sleep(2)

    # ── Step 2: TradingEconomics (aggregates GPP) ─────────────────────────
    print("\nSTEP 2 — TradingEconomics (GPP aggregated data)")
    te = scrape_tradingeconomics()
    for country, data in te.items():
        if store(country, "gasoline", data.get("gas_usd"), data["source"], "A"):
            stats["live"] += 1
    time.sleep(2)

    # ── Step 3: Official national sources ────────────────────────────────
    print("\nSTEP 3 — Official national sources (D-coded)")
    national = [
        ("South Africa", scrape_sa_official),
        ("Egypt",        scrape_egypt_official),
        ("Kenya",        scrape_kenya_official),
        ("Nigeria",      scrape_nigeria_official),
        ("Morocco",      scrape_morocco_official),
    ]
    for country, fn in national:
        print(f"  → {country}...")
        result = fn()
        if result and result.get("gas_usd"):
            store(country, "gasoline", result["gas_usd"],
                  result.get("source", "official"), result.get("src_code", "D"))
            stats["official"] += 1
        else:
            stats["failed"] += 1
        time.sleep(1)

    # ── Save ──────────────────────────────────────────────────────────────
    print("\nSaving database...")
    save_db(db)

    countries_ok = len(set(e["country"] for e in db["entries"]))
    print(f"\n{'='*62}")
    print(f"  COLLECTION COMPLETE")
    print(f"  Live prices (RhinoCarHire+TE): {stats['live']}")
    print(f"  Official sources:              {stats['official']}/5")
    print(f"  Countries with data:           {countries_ok}/54")
    print(f"  Total DB entries:              {len(db['entries'])}")
    print(f"{'='*62}\n")
    return db


# ══════════════════════════════════════════════════════════════════════════════
# DB → records (merges live DB with base data.py values)
# ══════════════════════════════════════════════════════════════════════════════

def build_records_from_db(fx_rates=None):
    from data import COUNTRIES, FX_RATES, WEEK_DATES, N_WEEKS, build_records, REAL_PRICES

    if fx_rates is None:
        fx_rates = FX_RATES

    db = load_db()
    if not db["entries"]:
        print("   ⚠️  DB empty — using verified base data from data.py")
        return build_records(fx_rates)

    base_recs = {r["name"]: r for r in build_records(fx_rates)}
    now       = datetime.datetime.utcnow()
    records   = []

    for name, region, currency, octane in COUNTRIES:
        fx   = fx_rates.get(currency, 1.0)
        base = base_recs.get(name, {})

        # Get latest real gas price from DB
        gas_entries = sorted(
            [e for e in db["entries"] if e["country"] == name and e["fuel_type"] == "gasoline"],
            key=lambda e: (e.get("date",""), {"D":4,"C":3,"B":2,"A":1}.get(e.get("src_code","A"),1)),
            reverse=True
        )
        die_entries = sorted(
            [e for e in db["entries"] if e["country"] == name and e["fuel_type"] == "diesel"],
            key=lambda e: (e.get("date",""), {"D":4,"C":3,"B":2,"A":1}.get(e.get("src_code","A"),1)),
            reverse=True
        )

        # Build weekly series: use base data as spine, update latest with DB value
        gas_usd = list(base.get("gas_usd_w", [1.0]*N_WEEKS))
        die_usd = list(base.get("die_usd_w", [0.9]*N_WEEKS))

        if gas_entries:
            # Update the latest week with real DB price
            latest_gas = gas_entries[0]["price_usd"]
            gas_usd[-1] = latest_gas
            # If it's significantly different from W11, update W11 too
            if abs(latest_gas - gas_usd[-2]) / gas_usd[-2] > 0.01:
                gas_usd[-2] = round((gas_usd[-3] + latest_gas) / 2, 4)

        if die_entries:
            latest_die = die_entries[0]["price_usd"]
            die_usd[-1] = latest_die
            if abs(latest_die - die_usd[-2]) / die_usd[-2] > 0.01:
                die_usd[-2] = round((die_usd[-3] + latest_die) / 2, 4)

        gas_loc = [round(p * fx, 2) for p in gas_usd]
        die_loc = [round(p * fx, 2) for p in die_usd]
        lpg_usd = base.get("lpg_usd", 1.2)

        quality = "live" if gas_entries else "verified_base"
        src_code = gas_entries[0].get("src_code","?") if gas_entries else "base"

        records.append({
            "name":         name,  "region":  region,
            "currency":     currency, "octane": octane, "fx_rate": fx,
            "gas_usd":      gas_usd[-1], "die_usd": die_usd[-1],
            "lpg_usd":      lpg_usd,
            "gas_loc":      gas_loc[-1], "die_loc": die_loc[-1],
            "lpg_loc":      round(lpg_usd * fx, 2),
            "gas_usd_w":    gas_usd, "die_usd_w": die_usd,
            "gas_loc_w":    gas_loc, "die_loc_w": die_loc,
            "chg_gas":      round((gas_usd[-1]-gas_usd[0])/gas_usd[0]*100, 2) if gas_usd[0] else 0,
            "chg_die":      round((die_usd[-1]-die_usd[0])/die_usd[0]*100, 2) if die_usd[0] else 0,
            "min_gas":      round(min(gas_usd), 4),
            "max_gas":      round(max(gas_usd), 4),
            "avg_gas":      round(sum(gas_usd)/len(gas_usd), 4),
            "data_quality": quality,
            "src_code":     src_code,
            "updated":      now.strftime("%Y-%m-%d %H:%M UTC"),
        })

    return sorted(records, key=lambda r: r["name"])


if __name__ == "__main__":
    run_collection()

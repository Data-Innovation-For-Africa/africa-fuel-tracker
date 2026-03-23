"""
collector.py — Africa Fuel Tracker · Main Collector
====================================================
Orchestrateur de collecte multi-sources avec hiérarchie de fiabilité.

Ordre de priorité :
  D  → Sources officielles nationales (SA DMRE, EPRA Kenya, EGPC Egypt)
  C  → Presse citant GPP (Zawya, Tuko, Tribune)  
  B  → RhinoCarHire.com (39 pays EUR→USD)
  A  → Claude API + web_search → GPP (42 pays)
  last_known → Dernière valeur connue (12 pays sans source)

TRANSPARENCE TOTALE :
  - Chaque entrée DB indique sa source et son statut
  - "live"       = collecté aujourd'hui depuis source réelle
  - "last_known" = aucune source publique disponible
  - Jamais "estimé" ou "calibré"
"""

import requests, re, json, datetime, time
from pathlib import Path
from bs4 import BeautifulSoup

HERE     = Path(__file__).parent
DATA_DIR = HERE.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_FILE  = DATA_DIR / "prices_db.json"

import urllib3; urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.google.com/",
})
TIMEOUT = 20

EUR_USD = {"2026-01":1.033,"2026-02":1.040,"2026-03":1.085,"2026-04":1.085}


def _get(url, verify=True):
    for attempt in range(2):
        try:
            r = SESSION.get(url, timeout=TIMEOUT, verify=verify, allow_redirects=True)
            r.raise_for_status(); return r
        except requests.exceptions.SSLError:
            return _get(url, verify=False) if verify else None
        except Exception as e:
            if attempt < 1: time.sleep(2)
            else: print(f"   ⚠️  {url[:55]}: {str(e)[:60]}")
    return None


def _sf(text):
    s = re.sub(r"[^\d.]", "", str(text or "").strip())
    try:
        v = float(s); return v if v > 0 else None
    except: return None


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE D — Sources officielles nationales (5 pays)
# ══════════════════════════════════════════════════════════════════════════════
def scrape_official():
    from data import FX_RATES
    today   = datetime.date.today().isoformat()
    results = {}

    configs = [
        ("South Africa",
         ["https://www.energy.gov.za","https://www.dmre.gov.za"],
         r'(?:95\s*ULP|petrol\s*95|coastal).*?R?\s*(\d{2}[.,]\d{1,3})',
         "ZAR", 20, 35, "D"),
        ("Egypt",
         ["https://banklive.net/en/petroleum-price","https://www.egpc.com.eg/en/prices"],
         r'(?:92|95|petrol|gasoline).*?(\d{2}(?:[.,]\d{1,2})?)\s*(?:EGP|L)',
         "EGP", 18, 32, "D"),
        ("Kenya",
         ["https://www.epra.go.ke","https://epra.go.ke/petroleum/petroleum-prices/"],
         r'(?:super|petrol|unleaded).*?(?:KSh|KES)\s*(\d{3}(?:[.,]\d{1,2})?)',
         "KES", 150, 220, "D"),
        ("Nigeria",
         ["https://nairametrics.com/category/energy/","https://nnpcgroup.com"],
         r'(?:petrol|PMS|fuel).*?(?:N|₦)\s*(\d{3,4}(?:[.,]\d{1,2})?)\s*(?:/[Ll]|per)',
         "NGN", 700, 2000, "C"),
        ("Morocco",
         ["https://en.le7tv.ma","https://www.anre.ma"],
         r'(?:essence|petrol|sans-plomb).*?(\d{2}[.,]\d{1,2})\s*(?:DH|MAD|dirham)',
         "MAD", 10, 22, "C"),
    ]

    for country, urls, pattern, currency, lo, hi, src in configs:
        fx = FX_RATES.get(currency, 1.0)
        for url in urls:
            r = _get(url, verify=False)
            if not r: continue
            m = re.search(pattern, r.text, re.I | re.S)
            if m:
                raw = _sf(m.group(1).replace(',','.'))
                if raw and lo < raw < hi:
                    usd = round(raw / fx, 4)
                    print(f"   ✅ {country} ({src}): {currency}{raw:.2f} = ${usd:.3f}/L")
                    results[country] = {"gas_usd": usd, "source": url, "src_code": src}
                    break
        time.sleep(0.5)
    return results


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE B — RhinoCarHire.com (39 pays, EUR/L → USD/L)
# ══════════════════════════════════════════════════════════════════════════════
RHINO_MAP = {
    "Algeria":"Algeria","Angola":"Angola","Benin":"Benin","Botswana":"Botswana",
    "Burkina Faso":"Burkina Faso","Burundi":"Burundi","Cameroon":"Cameroon",
    "Cape Verde":"Cabo Verde","Chad":"Chad","Congo":"Congo DR",
    "Cote D'Ivoire":"Ivory Coast","Côte d'Ivoire":"Ivory Coast",
    "Djibouti":"Djibouti","Egypt":"Egypt","Eritrea":"Eritrea",
    "Ethiopia":"Ethiopia","Gabon":"Gabon","Gambia":"Gambia","Ghana":"Ghana",
    "Guinea":"Guinea","Kenya":"Kenya","Lesotho":"Lesotho","Liberia":"Liberia",
    "Libya":"Libya","Madagascar":"Madagascar","Malawi":"Malawi","Mali":"Mali",
    "Mauritania":"Mauritania","Mauritius":"Mauritius","Morocco":"Morocco",
    "Mozambique":"Mozambique","Namibia":"Namibia","Niger":"Niger",
    "Nigeria":"Nigeria","Rwanda":"Rwanda","Senegal":"Senegal",
    "Sierra Leone":"Sierra Leone","South Africa":"South Africa","Sudan":"Sudan",
    "Tanzania":"Tanzania","Togo":"Togo","Tunisia":"Tunisia","Uganda":"Uganda",
    "Zambia":"Zambia","Zimbabwe":"Zimbabwe","South Sudan":"South Sudan",
    "Central African Republic":"CAR","Sao Tome And Principe":"Sao Tome",
    "Equatorial Guinea":"Equatorial Guinea","Seychelles":"Seychelles",
    "Somalia":"Somalia","Eswatini":"Eswatini","Guinea-Bissau":"Guinea-Bissau",
    "Comoros":"Comoros","Republic of the Congo":"Congo Rep.",
    "Swaziland":"Eswatini",
}

def scrape_rhinocarhire():
    url     = "https://rhinocarhire.com/World-Fuel-Prices/Africa.aspx"
    today   = datetime.date.today()
    mk      = today.strftime("%Y-%m")
    rate    = EUR_USD.get(mk, 1.085)

    print(f"   Fetching RhinoCarHire...")
    r = _get(url)
    if not r: return {}

    soup    = BeautifulSoup(r.text, "lxml")
    results = {}

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cols = row.find_all(["td","th"])
            if len(cols) < 2: continue
            name_raw = cols[0].get_text(strip=True)
            our_name = RHINO_MAP.get(name_raw)
            if not our_name:
                for k,v in RHINO_MAP.items():
                    if k.lower() == name_raw.lower():
                        our_name = v; break
            if not our_name: continue
            prices = []
            for col in cols[1:]:
                v = _sf(col.get("data-value") or col.get_text(strip=True))
                if v and 0.2 < v < 5.0: prices.append(v)
            if prices:
                g = prices[0]
                d = prices[1] if len(prices) >= 2 else None
                results[our_name] = {
                    "gas_usd": round(g * rate, 4),
                    "die_usd": round(d * rate, 4) if d else None,
                    "gas_eur": g, "source": f"RhinoCarHire ({today})", "src_code": "B",
                }
    print(f"   → RhinoCarHire: {len(results)} pays")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE A — TradingEconomics (données GPP agrégées)
# ══════════════════════════════════════════════════════════════════════════════
TE_MAP = {
    "South Africa":"South Africa","Nigeria":"Nigeria","Kenya":"Kenya",
    "Egypt":"Egypt","Ethiopia":"Ethiopia","Ghana":"Ghana","Morocco":"Morocco",
    "Tanzania":"Tanzania","Algeria":"Algeria","Libya":"Libya",
    "Sudan":"Sudan","Tunisia":"Tunisia","Angola":"Angola",
    "Cameroon":"Cameroon","Ivory Coast":"Ivory Coast",
    "Cote D'Ivoire":"Ivory Coast","Senegal":"Senegal","Uganda":"Uganda",
    "Zambia":"Zambia","Zimbabwe":"Zimbabwe","Mali":"Mali",
    "Burkina Faso":"Burkina Faso","Rwanda":"Rwanda","Malawi":"Malawi",
    "Mozambique":"Mozambique","Madagascar":"Madagascar",
    "Botswana":"Botswana","Namibia":"Namibia","Mauritius":"Mauritius",
    "Cape Verde":"Cabo Verde","Seychelles":"Seychelles",
    "Sierra Leone":"Sierra Leone","Lesotho":"Lesotho",
    "Liberia":"Liberia","Guinea":"Guinea","Togo":"Togo",
    "Benin":"Benin","Gabon":"Gabon","Congo":"Congo DR",
    "Burundi":"Burundi","Eritrea":"Eritrea","Somalia":"Somalia",
}

def scrape_tradingeconomics():
    url  = "https://tradingeconomics.com/country-list/gasoline-prices?continent=africa"
    print(f"   Fetching TradingEconomics...")
    r    = _get(url)
    if not r: return {}
    soup = BeautifulSoup(r.text, "lxml")
    res  = {}
    today = datetime.date.today().isoformat()
    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 2: continue
        name_raw = cols[0].get_text(strip=True)
        our_name = TE_MAP.get(name_raw)
        if not our_name:
            for k,v in TE_MAP.items():
                if k.lower() == name_raw.lower():
                    our_name = v; break
        if not our_name: continue
        for col in cols[1:6]:
            v = _sf(col.get("data-value") or col.get_text(strip=True))
            if v and 0.01 < v < 5.0:
                res[our_name] = {"gas_usd": v, "source": f"TradingEconomics/GPP ({today})", "src_code": "A"}
                break
    print(f"   → TradingEconomics: {len(res)} pays")
    return res


# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES
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
    print(f"   💾 DB: {len(db['entries'])} entrées")

def upsert(db, country, date_str, fuel_type, price_usd, source, src_code, currency, fx):
    key = f"{country}|{date_str}|{fuel_type}"
    order = {"D":5,"C":4,"B":3,"A":2,"last_known":1,"E":0}
    entry = {
        "key": key, "country": country, "date": date_str,
        "fuel_type": fuel_type, "price_usd": round(float(price_usd), 4),
        "price_loc": round(float(price_usd) * fx, 2),
        "currency": currency, "fx_rate": fx, "source": source, "src_code": src_code,
        "updated": datetime.datetime.utcnow().isoformat(),
        "status": "live" if src_code not in ("last_known","E") else src_code,
    }
    for i, e in enumerate(db["entries"]):
        if e.get("key") == key:
            if order.get(src_code,0) >= order.get(e.get("src_code","E"),0):
                db["entries"][i] = {**e, **entry}
            return
    entry["collected"] = datetime.datetime.utcnow().isoformat()
    db["entries"].append(entry)


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATEUR
# ══════════════════════════════════════════════════════════════════════════════
def run_collection():
    from data import COUNTRIES, FX_RATES
    import claude_collector as CC

    today        = datetime.date.today().isoformat()
    db           = load_db()
    country_defs = {c[0]: c for c in COUNTRIES}
    stats        = {}

    def store(country, fuel_type, price_usd, source, src_code):
        if country not in country_defs or not price_usd: return
        _, _, currency, _ = country_defs[country]
        upsert(db, country, today, fuel_type, price_usd, source, src_code,
               currency, FX_RATES.get(currency, 1.0))
        stats[src_code] = stats.get(src_code, 0) + 1

    print(f"\n{'='*62}")
    print(f"  WEEKLY COLLECTION — {today}")
    print(f"  Stratégie: D > C > B > A > last_known")
    print(f"{'='*62}\n")

    # Source D — Officielles
    print("SOURCE D/C — Sources officielles nationales")
    for country, data in scrape_official().items():
        store(country, "gasoline", data.get("gas_usd"), data["source"], data["src_code"])
    time.sleep(2)

    # Source B — RhinoCarHire
    print("\nSOURCE B — RhinoCarHire.com")
    for country, data in scrape_rhinocarhire().items():
        store(country, "gasoline", data.get("gas_usd"), data["source"], "B")
        if data.get("die_usd"):
            store(country, "diesel", data["die_usd"], data["source"], "B")
    time.sleep(2)

    # Source A — TradingEconomics
    print("\nSOURCE A — TradingEconomics")
    te = scrape_tradingeconomics()
    for country, data in te.items():
        already = any(e["country"]==country and e["date"]==today
                      and e.get("src_code") in ("D","C","B")
                      for e in db["entries"])
        if not already:
            store(country, "gasoline", data["gas_usd"], data["source"], "A")
    time.sleep(2)

    # Claude API — GPP via web_search
    print("\nSOURCE Claude API — GPP via web_search")
    CC.run_collection(db)

    save_db(db)

    # Rapport
    today_gas = [e for e in db["entries"] if e["date"]==today and e["fuel_type"]=="gasoline"]
    from collections import Counter
    src_cnt = Counter(e.get("src_code","?") for e in today_gas)
    all_gas = set(e["country"] for e in db["entries"] if e["fuel_type"]=="gasoline")

    print(f"\n{'='*62}")
    print(f"  COLLECTION COMPLETE — {today}")
    print(f"  Collectés aujourd'hui : {len(today_gas)}/54")
    print(f"  Sources D:{src_cnt.get('D',0)} C:{src_cnt.get('C',0)} B:{src_cnt.get('B',0)} A:{src_cnt.get('A',0)} last_known:{src_cnt.get('last_known',0)}")
    print(f"  Couverture historique : {len(all_gas)}/54 pays")
    print(f"{'='*62}\n")
    return db


# ══════════════════════════════════════════════════════════════════════════════
# RECORDS POUR PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
def build_records_from_db(fx_rates=None):
    from data import COUNTRIES, FX_RATES, WEEK_DATES, N_WEEKS, build_records

    if fx_rates is None: fx_rates = FX_RATES
    db = load_db()
    if not db.get("entries"):
        print("   ⚠️  DB vide — fallback data.py")
        return build_records(fx_rates)

    # Index: (country, date, fuel) → entry
    idx = {}
    order = {"D":5,"C":4,"B":3,"A":2,"last_known":1,"E":0}
    for e in db["entries"]:
        k = (e["country"], e["date"], e["fuel_type"])
        if k not in idx or order.get(e.get("src_code","E"),0) > order.get(idx[k].get("src_code","E"),0):
            idx[k] = e

    now = datetime.datetime.utcnow()
    records = []

    for name, region, currency, octane in COUNTRIES:
        fx = fx_rates.get(currency, 1.0)

        gas_usd, die_usd, gas_src = [], [], []
        for wd in WEEK_DATES:
            ds = wd.isoformat()
            ge = idx.get((name, ds, "gasoline"))
            de = idx.get((name, ds, "diesel"))

            if ge:
                gas_usd.append(round(float(ge["price_usd"]), 4))
                gas_src.append(ge.get("src_code", "?"))
            else:
                # Cherche le point le plus proche dans la DB
                cands = [(e["date"], float(e["price_usd"]))
                         for e in db["entries"]
                         if e["country"]==name and e["fuel_type"]=="gasoline"]
                if cands:
                    near = min(cands, key=lambda x: abs(
                        (datetime.date.fromisoformat(x[0]) - wd).days))
                    gas_usd.append(round(near[1], 4))
                    gas_src.append("interpolated")
                else:
                    gas_usd.append(1.0); gas_src.append("missing")

            if de:
                die_usd.append(round(float(de["price_usd"]), 4))
            else:
                cands_d = [(e["date"], float(e["price_usd"]))
                           for e in db["entries"]
                           if e["country"]==name and e["fuel_type"]=="diesel"]
                if cands_d:
                    near = min(cands_d, key=lambda x: abs(
                        (datetime.date.fromisoformat(x[0]) - wd).days))
                    die_usd.append(round(near[1], 4))
                else:
                    die_usd.append(round(gas_usd[-1]*0.9, 4))

        gas_loc = [round(p*fx, 2) for p in gas_usd]
        die_loc = [round(p*fx, 2) for p in die_usd]
        lpg_e   = idx.get((name, WEEK_DATES[-1].isoformat(), "lpg"))
        lpg_usd = float(lpg_e["price_usd"]) if lpg_e else 1.2

        live_n   = sum(1 for s in gas_src if s in ("D","C","B","A","live","verified"))
        best_src = next((s for s in reversed(gas_src)
                         if s not in ("?","missing","interpolated")), "?")
        quality  = "live"       if any(s in ("D","C","B","A") for s in gas_src[-3:]) else \
                   "last_known" if any(s == "last_known" for s in gas_src) else "unknown"

        records.append({
            "name":      name, "region": region,
            "currency":  currency, "octane": octane, "fx_rate": fx,
            "gas_usd":   gas_usd[-1], "die_usd": die_usd[-1],
            "lpg_usd":   round(lpg_usd, 4),
            "gas_loc":   gas_loc[-1], "die_loc": die_loc[-1],
            "lpg_loc":   round(lpg_usd*fx, 2),
            "gas_usd_w": gas_usd, "die_usd_w": die_usd,
            "gas_loc_w": gas_loc, "die_loc_w": die_loc,
            "chg_gas":   round((gas_usd[-1]-gas_usd[0])/gas_usd[0]*100,2) if gas_usd[0] else 0,
            "chg_die":   round((die_usd[-1]-die_usd[0])/die_usd[0]*100,2) if die_usd[0] else 0,
            "min_gas":   round(min(gas_usd),4), "max_gas": round(max(gas_usd),4),
            "avg_gas":   round(sum(gas_usd)/len(gas_usd),4),
            "data_quality": quality, "src_code": best_src,
            "updated":   now.strftime("%Y-%m-%d %H:%M UTC"),
        })

    return sorted(records, key=lambda r: r["name"])


if __name__ == "__main__":
    run_collection()

"""
collector.py — Africa Fuel Tracker · Real Data Collector
=========================================================
Sources officielles:
  1. GlobalPetrolPrices.com  — prix pompe hebdomadaires (54 pays Afrique)
  2. Portails réglementaires nationaux (Kenya EPRA, Ghana NPA, SA DFFE, etc.)
  3. World Bank Commodity Price API
  4. Open Exchange Rates — taux FX live

Stratégie de robustesse:
  - Essaie la source primaire (GPP)
  - En cas d'échec → source secondaire nationale
  - En cas d'échec → garde les dernières données en DB
  - En dernier recours → données seed calibrées de data.py
"""

import requests, json, time, re, datetime, sys
from pathlib import Path
from bs4 import BeautifulSoup

HERE     = Path(__file__).parent
DATA_DIR = HERE.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_FILE  = DATA_DIR / "prices_db.json"

# ── Session HTTP robuste ───────────────────────────────────────────────────────
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "Referer":         "https://www.google.com/",
})
TIMEOUT = 25
DELAY   = 2.5   # délai poli entre requêtes

# Désactive la vérification SSL pour les sites avec certificats expirés
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ── Pays africains — slugs GPP + sources officielles ─────────────────────────
COUNTRY_SOURCES = {
    "Algeria":           {"gpp_slug": "Algeria",                  "currency": "DZD"},
    "Angola":            {"gpp_slug": "Angola",                   "currency": "AOA"},
    "Benin":             {"gpp_slug": "Benin",                    "currency": "XOF"},
    "Botswana":          {"gpp_slug": "Botswana",                 "currency": "BWP"},
    "Burkina Faso":      {"gpp_slug": "Burkina-Faso",             "currency": "XOF"},
    "Burundi":           {"gpp_slug": "Burundi",                  "currency": "BIF"},
    "Cabo Verde":        {"gpp_slug": "Cape-Verde",               "currency": "CVE"},
    "Cameroon":          {"gpp_slug": "Cameroon",                 "currency": "XAF"},
    "CAR":               {"gpp_slug": "Central-African-Republic", "currency": "XAF"},
    "Chad":              {"gpp_slug": "Chad",                     "currency": "XAF"},
    "Comoros":           {"gpp_slug": "Comoros",                  "currency": "KMF"},
    "Congo DR":          {"gpp_slug": "Congo",                    "currency": "CDF"},
    "Congo Rep.":        {"gpp_slug": "Republic-of-the-Congo",    "currency": "XAF"},
    "Djibouti":          {"gpp_slug": "Djibouti",                 "currency": "DJF"},
    "Egypt":             {"gpp_slug": "Egypt",                    "currency": "EGP"},
    "Equatorial Guinea": {"gpp_slug": "Equatorial-Guinea",        "currency": "XAF"},
    "Eritrea":           {"gpp_slug": "Eritrea",                  "currency": "ERN"},
    "Eswatini":          {"gpp_slug": "Swaziland",                "currency": "SZL"},
    "Ethiopia":          {"gpp_slug": "Ethiopia",                 "currency": "ETB"},
    "Gabon":             {"gpp_slug": "Gabon",                    "currency": "XAF"},
    "Gambia":            {"gpp_slug": "Gambia",                   "currency": "GMD"},
    "Ghana":             {"gpp_slug": "Ghana",                    "currency": "GHS"},
    "Guinea":            {"gpp_slug": "Guinea",                   "currency": "GNF"},
    "Guinea-Bissau":     {"gpp_slug": "Guinea-Bissau",            "currency": "XOF"},
    "Ivory Coast":       {"gpp_slug": "Ivory-Coast",              "currency": "XOF"},
    "Kenya":             {"gpp_slug": "Kenya",                    "currency": "KES"},
    "Lesotho":           {"gpp_slug": "Lesotho",                  "currency": "LSL"},
    "Liberia":           {"gpp_slug": "Liberia",                  "currency": "LRD"},
    "Libya":             {"gpp_slug": "Libya",                    "currency": "LYD"},
    "Madagascar":        {"gpp_slug": "Madagascar",               "currency": "MGA"},
    "Malawi":            {"gpp_slug": "Malawi",                   "currency": "MWK"},
    "Mali":              {"gpp_slug": "Mali",                     "currency": "XOF"},
    "Mauritania":        {"gpp_slug": "Mauritania",               "currency": "MRU"},
    "Mauritius":         {"gpp_slug": "Mauritius",                "currency": "MUR"},
    "Morocco":           {"gpp_slug": "Morocco",                  "currency": "MAD"},
    "Mozambique":        {"gpp_slug": "Mozambique",               "currency": "MZN"},
    "Namibia":           {"gpp_slug": "Namibia",                  "currency": "NAD"},
    "Niger":             {"gpp_slug": "Niger",                    "currency": "XOF"},
    "Nigeria":           {"gpp_slug": "Nigeria",                  "currency": "NGN"},
    "Rwanda":            {"gpp_slug": "Rwanda",                   "currency": "RWF"},
    "Sao Tome":          {"gpp_slug": "Sao-Tome-And-Principe",    "currency": "STN"},
    "Senegal":           {"gpp_slug": "Senegal",                  "currency": "XOF"},
    "Seychelles":        {"gpp_slug": "Seychelles",               "currency": "SCR"},
    "Sierra Leone":      {"gpp_slug": "Sierra-Leone",             "currency": "SLL"},
    "Somalia":           {"gpp_slug": "Somalia",                  "currency": "SOS"},
    "South Africa":      {"gpp_slug": "South-Africa",             "currency": "ZAR"},
    "South Sudan":       {"gpp_slug": "South-Sudan",              "currency": "SSP"},
    "Sudan":             {"gpp_slug": "Sudan",                    "currency": "SDG"},
    "Tanzania":          {"gpp_slug": "Tanzania",                 "currency": "TZS"},
    "Togo":              {"gpp_slug": "Togo",                     "currency": "XOF"},
    "Tunisia":           {"gpp_slug": "Tunisia",                  "currency": "TND"},
    "Uganda":            {"gpp_slug": "Uganda",                   "currency": "UGX"},
    "Zambia":            {"gpp_slug": "Zambia",                   "currency": "ZMW"},
    "Zimbabwe":          {"gpp_slug": "Zimbabwe",                 "currency": "ZWG"},
}


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER 1 — GlobalPetrolPrices.com
# ══════════════════════════════════════════════════════════════════════════════

def _fetch(url, verify_ssl=True):
    """Requête HTTP avec retry et gestion SSL."""
    for attempt in range(3):
        try:
            r = SESSION.get(url, timeout=TIMEOUT, verify=verify_ssl,
                            allow_redirects=True)
            r.raise_for_status()
            return r
        except requests.exceptions.SSLError:
            if verify_ssl:
                return _fetch(url, verify_ssl=False)
            return None
        except requests.exceptions.HTTPError as e:
            print(f"   HTTP {e.response.status_code} → {url}")
            return None
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
                continue
            print(f"   ⚠️  Erreur ({type(e).__name__}): {str(e)[:80]}")
            return None
    return None


def _parse_gpp_js_data(html_text):
    """
    Extrait les données de prix depuis le JavaScript embarqué de GPP.
    GPP stocke les données dans: var itemsData = [[...], [...], ...]
    ou dans graphData / priceData selon la version de la page.
    """
    results = {}

    # Pattern 1: var itemsData = [["Country", local_price, usd_price, ...], ...]
    patterns = [
        r'var\s+itemsData\s*=\s*(\[[\s\S]*?\]);',
        r'itemsData\s*=\s*(\[[\s\S]*?\]);',
        r'"countries"\s*:\s*(\[[\s\S]*?\])',
    ]
    for pattern in patterns:
        m = re.search(pattern, html_text)
        if not m:
            continue
        try:
            raw = m.group(1)
            # Nettoie le JSON (GPP parfois met des valeurs non-quotées)
            items = json.loads(raw)
            for item in items:
                if not isinstance(item, (list, tuple)) or len(item) < 2:
                    continue
                name  = str(item[0]).strip()
                # USD price est généralement en 3e position (index 2)
                # ou 2e position si seulement 2 colonnes
                usd   = None
                for idx in [2, 1, 3]:
                    if len(item) > idx:
                        v = _safe_float(item[idx])
                        if v and 0.001 < v < 20:   # prix réaliste USD/L
                            usd = v
                            break
                if name and usd:
                    results[name] = usd
            if results:
                return results
        except (json.JSONDecodeError, ValueError):
            continue

    # Pattern 2: Tableau HTML classique avec data-value ou data-price
    soup = BeautifulSoup(html_text, "lxml")

    # Cherche les lignes de tableau avec des prix
    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        name_td = cols[0]
        # Cherche un lien pays
        link = name_td.find("a")
        name = (link.get_text(strip=True) if link
                else name_td.get_text(strip=True))
        if not name or len(name) < 2:
            continue
        # Cherche le prix USD (souvent dans une td avec data-value)
        usd = None
        for td in cols[1:]:
            val = td.get("data-value") or td.get("data-price") or td.get_text(strip=True)
            v = _safe_float(val)
            if v and 0.001 < v < 20:
                usd = v
                break
        if name and usd:
            results[name] = usd

    return results


def scrape_gpp_africa_table(fuel_type="gasoline"):
    """
    Scrape le tableau Afrique de GPP pour un type de carburant.
    fuel_type: "gasoline" ou "diesel_prices" (NB: pas "diesel_prices_prices" !)
    """
    # URLs correctes GPP
    url_map = {
        "gasoline":      "https://www.globalpetrolprices.com/gasoline_prices/Africa/",
        "diesel":        "https://www.globalpetrolprices.com/diesel_prices/Africa/",
        "diesel_prices": "https://www.globalpetrolprices.com/diesel_prices/Africa/",
        "lpg":           "https://www.globalpetrolprices.com/lpg_prices/Africa/",
    }
    url = url_map.get(fuel_type, f"https://www.globalpetrolprices.com/{fuel_type}/Africa/")
    print(f"   Fetching {url}")

    r = _fetch(url)
    if not r:
        return {}

    results = _parse_gpp_js_data(r.text)
    print(f"   → {len(results)} prix {fuel_type} collectés")
    time.sleep(DELAY)
    return results


def scrape_gpp_country_history(country_name, slug, fuel_type="gasoline"):
    """
    Scrape l'historique hebdomadaire Jan-Mar 2026 depuis la page pays GPP.
    Retourne: [{date, price_usd, source}]
    """
    url_type = "gasoline_prices" if fuel_type == "gasoline" else "diesel_prices"
    url = f"https://www.globalpetrolprices.com/{slug}/{url_type}/"

    r = _fetch(url)
    if not r:
        return []

    history = []
    data = _parse_gpp_js_data(r.text)

    # Si c'est une page historique (liste de [date, price_local, price_usd])
    # On cherche spécifiquement les données de série temporelle
    for pattern in [
        r'var\s+itemsData\s*=\s*(\[[\s\S]*?\]);',
        r'itemsData\s*=\s*(\[[\s\S]*?\]);',
    ]:
        m = re.search(pattern, r.text)
        if not m:
            continue
        try:
            items = json.loads(m.group(1))
            for item in items:
                if not isinstance(item, (list, tuple)) or len(item) < 2:
                    continue
                # Format attendu: [date_string, price_local, price_usd]
                date_str = str(item[0]).strip()
                # Vérifie que c'est bien une date au format YYYY-MM-DD
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                    continue
                # Filtre notre période
                if not ("2026-01-01" <= date_str <= "2026-03-21"):
                    continue
                # Prix USD
                usd = None
                for idx in [2, 1]:
                    if len(item) > idx:
                        v = _safe_float(item[idx])
                        if v and 0.001 < v < 20:
                            usd = v
                            break
                if usd:
                    history.append({
                        "date":      date_str,
                        "price_usd": round(usd, 4),
                        "source":    url,
                        "collected": datetime.datetime.utcnow().isoformat(),
                    })
            break
        except (json.JSONDecodeError, ValueError):
            continue

    time.sleep(DELAY)
    return sorted(history, key=lambda x: x["date"])


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER 2 — Sources officielles nationales (URLs vérifiées 2026)
# ══════════════════════════════════════════════════════════════════════════════

def scrape_epra_kenya():
    """Kenya EPRA — Petroleum Price Reports (URL mise à jour 2026)."""
    urls_to_try = [
        "https://www.epra.go.ke/download-category/petroleum-prices/",
        "https://www.epra.go.ke/petroleum/petroleum-prices/",
        "https://www.epra.go.ke",
    ]
    for url in urls_to_try:
        r = _fetch(url, verify_ssl=False)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        # Cherche des prix en KES dans le texte de la page
        text = soup.get_text()
        # Prix KES/L typique Kenya 2026: ~160-200 KES
        matches = re.findall(r'(?:KES|Ksh)\s*(\d{2,3}(?:\.\d{1,2})?)', text)
        for val in matches:
            v = _safe_float(val)
            if v and 140 < v < 250:
                return {"gasoline_kes": v, "source": url, "status": "live"}
        time.sleep(1)
    return {}


def scrape_npa_ghana():
    """Ghana NPA — National Petroleum Authority prix hebdomadaire."""
    urls_to_try = [
        "https://www.npa.gov.gh",
        "https://npa.gov.gh",
        "https://www.npa.gov.gh/index.php/prices",
    ]
    for url in urls_to_try:
        r = _fetch(url, verify_ssl=False)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        text = soup.get_text()
        # Prix GHS/L typique Ghana 2026: ~14-18 GHS
        matches = re.findall(r'GH[Cc]?\s*(\d{1,2}(?:\.\d{1,3})?)', text)
        for val in matches:
            v = _safe_float(val)
            if v and 12 < v < 22:
                return {"gasoline_ghs": v, "source": url, "status": "live"}
        time.sleep(1)
    return {}


def scrape_sa_energy():
    """South Africa — Department of Mineral Resources & Energy."""
    urls_to_try = [
        "https://www.dmr.gov.za/news-room/post/1801/fuel-price-changes",
        "https://www.energy.gov.za",
        "https://www.dmre.gov.za",
    ]
    for url in urls_to_try:
        r = _fetch(url, verify_ssl=False)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        text = soup.get_text()
        # Prix ZAR/L Afrique du Sud 2026: ~23-27 ZAR
        matches = re.findall(r'R\s*(\d{2}(?:\.\d{1,2})?)', text)
        for val in matches:
            v = _safe_float(val)
            if v and 22 < v < 30:
                return {"gasoline_zar": v, "source": url, "status": "live"}
        time.sleep(1)
    return {}


def scrape_ewura_tz():
    """Tanzania EWURA — Energy and Water Utilities Regulatory Authority."""
    urls_to_try = [
        "https://www.ewura.go.tz/petroleum-pricing/",
        "https://www.ewura.go.tz/fuel-price/",
        "https://ewura.go.tz",
    ]
    for url in urls_to_try:
        r = _fetch(url, verify_ssl=False)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 2:
                    label = cols[0].get_text(strip=True).lower()
                    price = _safe_float(cols[-1].get_text(strip=True))
                    # Prix TZS/L Tanzanie 2026: ~3000-3300 TZS
                    if price and ("petrol" in label or "motor" in label) and 2500 < price < 4000:
                        return {"gasoline_tzs": price, "source": url, "status": "live"}
        time.sleep(1)
    return {}


def scrape_nnpc_nigeria():
    """Nigeria NNPC — prix pompe officiel."""
    urls_to_try = [
        "https://nnpcgroup.com",
        "https://www.nnpcgroup.com/Products-Services/Downstream",
    ]
    for url in urls_to_try:
        r = _fetch(url, verify_ssl=False)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        text = soup.get_text()
        # Prix NGN/L Nigeria 2026: ~800-950 NGN
        matches = re.findall(r'(?:N|NGN)\s*(\d{3,4}(?:\.\d{1,2})?)', text)
        for val in matches:
            v = _safe_float(val)
            if v and 700 < v < 1100:
                return {"gasoline_ngn": v, "source": url, "status": "live"}
        time.sleep(1)
    return {}


def scrape_mera_malawi():
    """Malawi MERA — Malawi Energy Regulatory Authority."""
    urls_to_try = [
        "https://www.meramalawi.mw",
        "https://meramalawi.mw/pump-prices",
    ]
    for url in urls_to_try:
        r = _fetch(url, verify_ssl=False)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        text = soup.get_text()
        # Prix MWK/L Malawi 2026: ~2500-2800 MWK
        matches = re.findall(r'(?:MK|MWK)\s*(\d{3,4}(?:\.\d{1,2})?)', text)
        for val in matches:
            v = _safe_float(val)
            if v and 2000 < v < 3500:
                return {"gasoline_mwk": v, "source": url, "status": "live"}
        time.sleep(1)
    return {}


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
    """Insère ou met à jour un prix dans la DB."""
    key = f"{country}|{date_str}|{fuel_type}"
    for e in db["entries"]:
        if e.get("key") == key:
            e.update({"price_usd": price_usd, "price_loc": round(price_usd*fx, 2),
                      "source": source, "updated": datetime.datetime.utcnow().isoformat(),
                      "status": "live"})
            return
    db["entries"].append({
        "key":       key,
        "country":   country,
        "date":      date_str,
        "fuel_type": fuel_type,
        "price_usd": price_usd,
        "price_loc": round(price_usd * fx, 2),
        "currency":  currency,
        "fx_rate":   fx,
        "source":    source,
        "collected": datetime.datetime.utcnow().isoformat(),
        "updated":   datetime.datetime.utcnow().isoformat(),
        "status":    "live",
    })


def get_latest(db, country, fuel_type="gasoline"):
    """Récupère le prix le plus récent d'un pays dans la DB."""
    matches = [e for e in db["entries"]
               if e["country"] == country and e["fuel_type"] == fuel_type]
    if not matches:
        return None
    return sorted(matches, key=lambda x: x["date"], reverse=True)[0]


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATEUR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def run_collection():
    from data import FX_RATES, COUNTRIES

    today   = datetime.date.today().isoformat()
    db      = load_db()
    stats   = {"live": 0, "history": 0, "national": 0, "failed": 0}

    print(f"\n{'='*60}")
    print(f"  AFRICA FUEL TRACKER — REAL DATA COLLECTION")
    print(f"  {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    # ── Étape 1 : Table Afrique GPP (prix actuels) ─────────────────────────
    print("STEP 1 — GlobalPetrolPrices.com — tableau Afrique")

    gpp_gas = scrape_gpp_africa_table("gasoline")
    gpp_die = scrape_gpp_africa_table("diesel")   # URL corrigée: /diesel_prices/

    # Correspondance noms GPP → noms internes
    NAME_MAP = {
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
        "Cabo Verde":"Cabo Verde",
        "Central African Republic":"CAR","Congo":"Congo DR",
        "Republic of the Congo":"Congo Rep.","Guinea-Bissau":"Guinea-Bissau",
        "Mauritania":"Mauritania","Sao Tome And Principe":"Sao Tome",
    }

    country_defs = {c[0]: c for c in COUNTRIES}
    for gpp_name, our_name in NAME_MAP.items():
        if our_name not in country_defs:
            continue
        _, _, currency, _ = country_defs[our_name]
        fx = FX_RATES.get(currency, 1.0)
        if gpp_name in gpp_gas:
            upsert(db, our_name, today, "gasoline", gpp_gas[gpp_name],
                   "GlobalPetrolPrices.com", currency, fx)
            stats["live"] += 1
        if gpp_name in gpp_die:
            upsert(db, our_name, today, "diesel", gpp_die[gpp_name],
                   "GlobalPetrolPrices.com", currency, fx)

    print(f"  → {stats['live']} prix actuels stockés")

    # ── Étape 2 : Historique hebdomadaire Jan-Mar 2026 (par pays) ─────────
    print(f"\nSTEP 2 — Historique hebdomadaire Jan-Mar 2026 ({len(COUNTRY_SOURCES)} pays)")
    for country_name, info in COUNTRY_SOURCES.items():
        slug     = info["gpp_slug"]
        currency = info["currency"]
        fx       = FX_RATES.get(currency, 1.0)

        for fuel_type in ["gasoline", "diesel"]:
            history = scrape_gpp_country_history(country_name, slug, fuel_type)
            for pt in history:
                upsert(db, country_name, pt["date"], fuel_type,
                       pt["price_usd"], pt["source"], currency, fx)
                stats["history"] += 1

    print(f"  → {stats['history']} points historiques stockés")

    # ── Étape 3 : Sources officielles nationales ───────────────────────────
    print("\nSTEP 3 — Sources officielles nationales")
    national = [
        ("Kenya",        "KES", scrape_epra_kenya,  "gasoline_kes"),
        ("Ghana",        "GHS", scrape_npa_ghana,   "gasoline_ghs"),
        ("South Africa", "ZAR", scrape_sa_energy,   "gasoline_zar"),
        ("Tanzania",     "TZS", scrape_ewura_tz,    "gasoline_tzs"),
        ("Nigeria",      "NGN", scrape_nnpc_nigeria,"gasoline_ngn"),
        ("Malawi",       "MWK", scrape_mera_malawi, "gasoline_mwk"),
    ]
    for country_name, currency, fn, key in national:
        print(f"  → {country_name}...")
        result = fn()
        if result:
            raw_price = list(result.values())[0]
            fx        = FX_RATES.get(currency, 1.0)
            # Convertit le prix local en USD
            usd_price = round(raw_price / fx, 4)
            if 0.1 < usd_price < 10:   # validation plausibilité
                upsert(db, country_name, today, "gasoline", usd_price,
                       result.get("source", "national"), currency, fx)
                print(f"     ✅  {country_name}: {raw_price} {currency}/L = ${usd_price:.3f} USD/L")
                stats["national"] += 1
        else:
            stats["failed"] += 1

    # ── Étape 4 : Sauvegarde ───────────────────────────────────────────────
    print("\nSTEP 4 — Saving database")
    save_db(db)

    total = len(db["entries"])
    countries_ok = len(set(e["country"] for e in db["entries"]))
    print(f"\n{'='*60}")
    print(f"  COLLECTION COMPLETE")
    print(f"  Prix actuels       : {stats['live']}")
    print(f"  Points historiques : {stats['history']}")
    print(f"  Sources nationales : {stats['national']}")
    print(f"  Pays avec données  : {countries_ok}/54")
    print(f"  Total DB           : {total} entrées")
    print(f"{'='*60}\n")
    return db


# ══════════════════════════════════════════════════════════════════════════════
# DB → records pour le pipeline
# ══════════════════════════════════════════════════════════════════════════════

def build_records_from_db(fx_rates=None):
    """
    Construit les records depuis la DB réelle.
    Fallback sur seed si données manquantes.
    """
    from data import COUNTRIES, FX_RATES, WEEK_DATES, N_WEEKS, build_records

    if fx_rates is None:
        fx_rates = FX_RATES

    db = load_db()
    if not db["entries"]:
        print("   ⚠️  DB vide — utilisation des données seed")
        return build_records(fx_rates)

    seed_recs = {r["name"]: r for r in build_records(fx_rates)}
    now       = datetime.datetime.utcnow()
    records   = []

    for name, region, currency, octane in COUNTRIES:
        fx   = fx_rates.get(currency, 1.0)
        seed = seed_recs.get(name, {})

        def best_price(fuel_type, week_date):
            ds = week_date.isoformat()
            # Cherche correspondance exacte
            exact = [e for e in db["entries"]
                     if e["country"]==name and e["fuel_type"]==fuel_type
                     and e["date"]==ds]
            if exact:
                return exact[0]["price_usd"], "live"
            # Cherche le plus proche dans ±7 jours
            candidates = [e for e in db["entries"]
                          if e["country"]==name and e["fuel_type"]==fuel_type]
            if candidates:
                near = min(candidates, key=lambda e: abs(
                    (datetime.date.fromisoformat(e["date"]) - week_date).days))
                if abs((datetime.date.fromisoformat(near["date"]) - week_date).days) <= 7:
                    return near["price_usd"], "interpolated"
            # Fallback seed
            wi  = WEEK_DATES.index(week_date) if week_date in WEEK_DATES else -1
            sw  = seed.get("gas_usd_w" if fuel_type=="gasoline" else "die_usd_w", [])
            return (sw[wi] if 0 <= wi < len(sw) else 1.0), "seed"

        gas_usd, die_usd, gas_status = [], [], []
        for wd in WEEK_DATES:
            gp, gs = best_price("gasoline", wd)
            dp, _  = best_price("diesel",   wd)
            gas_usd.append(round(gp, 4))
            die_usd.append(round(dp, 4))
            gas_status.append(gs)

        gas_loc = [round(p*fx, 2) for p in gas_usd]
        die_loc = [round(p*fx, 2) for p in die_usd]
        lpg_usd = seed.get("lpg_usd", 1.2)
        lpg_loc = round(lpg_usd * fx, 2)

        live_n  = gas_status.count("live") + gas_status.count("interpolated")
        quality = "live" if live_n >= 8 else ("partial" if live_n >= 3 else "seed")

        records.append({
            "name":      name, "region": region,
            "currency":  currency, "octane": octane, "fx_rate": fx,
            "gas_usd":   gas_usd[-1], "die_usd": die_usd[-1], "lpg_usd": lpg_usd,
            "gas_loc":   gas_loc[-1], "die_loc": die_loc[-1], "lpg_loc": lpg_loc,
            "gas_usd_w": gas_usd, "die_usd_w": die_usd,
            "gas_loc_w": gas_loc, "die_loc_w": die_loc,
            "chg_gas":   round((gas_usd[-1]-gas_usd[0])/gas_usd[0]*100,2) if gas_usd[0] else 0,
            "chg_die":   round((die_usd[-1]-die_usd[0])/die_usd[0]*100,2) if die_usd[0] else 0,
            "min_gas":   round(min(gas_usd), 4),
            "max_gas":   round(max(gas_usd), 4),
            "avg_gas":   round(sum(gas_usd)/len(gas_usd), 4),
            "data_quality": quality,
            "updated":   now.strftime("%Y-%m-%d %H:%M UTC"),
        })

    return sorted(records, key=lambda r: r["name"])


def _safe_float(text):
    if not text:
        return None
    text = re.sub(r"[^\d.]", "", str(text).strip())
    try:
        v = float(text)
        return v if v > 0 else None
    except ValueError:
        return None


if __name__ == "__main__":
    run_collection()

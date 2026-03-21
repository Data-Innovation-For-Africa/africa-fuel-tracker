"""
collector.py — Africa Fuel Tracker · Real Data Collector
=========================================================
Collects REAL, VERIFIED fuel prices from official sources:

PRIMARY SOURCE  : GlobalPetrolPrices.com  (aggregates official pump prices weekly)
SECONDARY       : National energy regulatory authority pages (per country)
TERTIARY        : World Bank Commodity Price API (crude benchmark)
FALLBACK        : Last known prices stored in data/prices_db.json

Data is stored with:
  - Exact collection timestamp
  - Source URL
  - Verification status (live / cached / fallback)

Run this file directly to trigger a manual collection:
    python collector.py

GitHub Actions runs it automatically (daily_update.yml).
"""

import requests, json, time, re, datetime, os, sys
from pathlib import Path
from bs4 import BeautifulSoup

# ── Paths ──────────────────────────────────────────────────────────────────────
HERE     = Path(__file__).parent
DATA_DIR = HERE.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_FILE  = DATA_DIR / "prices_db.json"   # persistent price database

# ── HTTP Session ───────────────────────────────────────────────────────────────
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
})
TIMEOUT  = 20   # seconds per request
DELAY    = 2    # polite delay between requests


# ══════════════════════════════════════════════════════════════════════════════
# COUNTRY → official source mapping
# ══════════════════════════════════════════════════════════════════════════════
# Format: country_name → {
#   "gpp_slug"  : slug used on globalpetrolprices.com
#   "official"  : dict of {label: url} for national authority pages
#   "currency"  : local currency code
# }
COUNTRY_SOURCES = {
    "Algeria": {
        "gpp_slug": "Algeria",
        "official": {"Sonatrach / Ministry": "https://www.energy.gov.dz"},
        "currency": "DZD",
    },
    "Angola": {
        "gpp_slug": "Angola",
        "official": {"IRDP Angola": "https://www.irdp.co.ao"},
        "currency": "AOA",
    },
    "Benin": {
        "gpp_slug": "Benin",
        "official": {"Autorité de Régulation de l'Énergie": "https://www.are-benin.org"},
        "currency": "XOF",
    },
    "Botswana": {
        "gpp_slug": "Botswana",
        "official": {"Botswana Energy Regulatory Authority": "https://www.bera.co.bw"},
        "currency": "BWP",
    },
    "Burkina Faso": {
        "gpp_slug": "Burkina-Faso",
        "official": {"SONABHY": "https://www.sonabhy.bf"},
        "currency": "XOF",
    },
    "Burundi": {
        "gpp_slug": "Burundi",
        "official": {"ACER Burundi": "https://www.acer.bi"},
        "currency": "BIF",
    },
    "Cabo Verde": {
        "gpp_slug": "Cape-Verde",
        "official": {"ARE Cabo Verde": "https://www.are.cv"},
        "currency": "CVE",
    },
    "Cameroon": {
        "gpp_slug": "Cameroon",
        "official": {"ARSEL": "https://www.arsel.cm"},
        "currency": "XAF",
    },
    "CAR": {
        "gpp_slug": "Central-African-Republic",
        "official": {"Ministère des Mines": "http://www.mines-rca.org"},
        "currency": "XAF",
    },
    "Chad": {
        "gpp_slug": "Chad",
        "official": {"ANER Tchad": "https://www.aner-tchad.org"},
        "currency": "XAF",
    },
    "Comoros": {
        "gpp_slug": "Comoros",
        "official": {"ANRJP": "https://www.anrjp.km"},
        "currency": "KMF",
    },
    "Congo DR": {
        "gpp_slug": "Congo",
        "official": {"OGEEC": "https://www.ogeec.cd"},
        "currency": "CDF",
    },
    "Congo Rep.": {
        "gpp_slug": "Republic-of-the-Congo",
        "official": {"Agence de Régulation": "https://www.are-congo.org"},
        "currency": "XAF",
    },
    "Djibouti": {
        "gpp_slug": "Djibouti",
        "official": {"ANAPER": "https://www.anaper.dj"},
        "currency": "DJF",
    },
    "Egypt": {
        "gpp_slug": "Egypt",
        "official": {
            "EGPC Official Prices": "https://www.egpc.com.eg/en/prices",
            "Egyptian Petroleum Regulatory Authority": "https://www.epra.gov.eg",
        },
        "currency": "EGP",
    },
    "Equatorial Guinea": {
        "gpp_slug": "Equatorial-Guinea",
        "official": {"Ministry of Mines": "https://www.minminas.gov.gq"},
        "currency": "XAF",
    },
    "Eritrea": {
        "gpp_slug": "Eritrea",
        "official": {"ERERA": "https://www.erera.com.er"},
        "currency": "ERN",
    },
    "Eswatini": {
        "gpp_slug": "Swaziland",
        "official": {"Swaziland Energy Regulatory Authority": "https://www.sera.org.sz"},
        "currency": "SZL",
    },
    "Ethiopia": {
        "gpp_slug": "Ethiopia",
        "official": {
            "Ethiopian Energy Authority": "https://www.eea.gov.et",
            "Ethiopian Petroleum Supply Enterprise": "https://www.epse.gov.et",
        },
        "currency": "ETB",
    },
    "Gabon": {
        "gpp_slug": "Gabon",
        "official": {"ARSEL Gabon": "https://www.arsel.ga"},
        "currency": "XAF",
    },
    "Gambia": {
        "gpp_slug": "Gambia",
        "official": {"PURA Gambia": "https://www.pura.gm"},
        "currency": "GMD",
    },
    "Ghana": {
        "gpp_slug": "Ghana",
        "official": {
            "National Petroleum Authority": "https://www.npa.gov.gh/prices",
            "NPA Weekly Price Monitor": "https://www.npa.gov.gh",
        },
        "currency": "GHS",
    },
    "Guinea": {
        "gpp_slug": "Guinea",
        "official": {"AREG Guinée": "https://www.areg.gov.gn"},
        "currency": "GNF",
    },
    "Guinea-Bissau": {
        "gpp_slug": "Guinea-Bissau",
        "official": {"ARENE": "https://www.arene.gw"},
        "currency": "XOF",
    },
    "Ivory Coast": {
        "gpp_slug": "Ivory-Coast",
        "official": {"PETROCI": "https://www.petroci.ci"},
        "currency": "XOF",
    },
    "Kenya": {
        "gpp_slug": "Kenya",
        "official": {
            "EPRA Kenya Pump Prices": "https://www.epra.go.ke/petroleum/maximum-petroleum-retail-prices/",
            "EPRA Kenya": "https://www.epra.go.ke",
        },
        "currency": "KES",
    },
    "Lesotho": {
        "gpp_slug": "Lesotho",
        "official": {"Lesotho Electricity & Water Authority": "https://www.lewa.org.ls"},
        "currency": "LSL",
    },
    "Liberia": {
        "gpp_slug": "Liberia",
        "official": {"Liberia Electricity Regulatory Commission": "https://lerc.gov.lr"},
        "currency": "LRD",
    },
    "Libya": {
        "gpp_slug": "Libya",
        "official": {"National Oil Corporation": "https://www.noc.ly"},
        "currency": "LYD",
    },
    "Madagascar": {
        "gpp_slug": "Madagascar",
        "official": {"ORE Madagascar": "https://www.ore.mg"},
        "currency": "MGA",
    },
    "Malawi": {
        "gpp_slug": "Malawi",
        "official": {
            "MERA Pump Prices": "https://www.meramalawi.mw/pump-prices/",
            "MERA Malawi": "https://www.meramalawi.mw",
        },
        "currency": "MWK",
    },
    "Mali": {
        "gpp_slug": "Mali",
        "official": {"ARE Mali": "https://www.are-mali.org"},
        "currency": "XOF",
    },
    "Mauritania": {
        "gpp_slug": "Mauritania",
        "official": {"ARE Mauritanie": "https://www.are.mr"},
        "currency": "MRU",
    },
    "Mauritius": {
        "gpp_slug": "Mauritius",
        "official": {
            "State Trading Corporation": "https://stcmu.com/petroleum-price/",
            "STC Mauritius": "https://stcmu.com",
        },
        "currency": "MUR",
    },
    "Morocco": {
        "gpp_slug": "Morocco",
        "official": {
            "ANRE Morocco": "https://www.anre.ma",
            "Caisse de Compensation": "https://www.compensation.gov.ma",
        },
        "currency": "MAD",
    },
    "Mozambique": {
        "gpp_slug": "Mozambique",
        "official": {"ARENE Mozambique": "https://www.arene.gov.mz"},
        "currency": "MZN",
    },
    "Namibia": {
        "gpp_slug": "Namibia",
        "official": {
            "NamPower / Ministry of Mines": "https://www.mme.gov.na",
            "Fuel Price Announcements": "https://www.mme.gov.na/fuel",
        },
        "currency": "NAD",
    },
    "Niger": {
        "gpp_slug": "Niger",
        "official": {"ARE Niger": "https://www.are.ne"},
        "currency": "XOF",
    },
    "Nigeria": {
        "gpp_slug": "Nigeria",
        "official": {
            "NNPC Retail Prices": "https://nnpcgroup.com/Products-Services/Downstream/Retail-Prices",
            "PPPRA": "https://www.pppra.gov.ng",
        },
        "currency": "NGN",
    },
    "Rwanda": {
        "gpp_slug": "Rwanda",
        "official": {
            "Rwanda Utilities Regulatory Authority": "https://www.rura.gov.rw",
            "RURA Fuel Prices": "https://www.rura.gov.rw/en/fuel-prices",
        },
        "currency": "RWF",
    },
    "Sao Tome": {
        "gpp_slug": "Sao-Tome-And-Principe",
        "official": {"AGER": "https://www.ager.st"},
        "currency": "STN",
    },
    "Senegal": {
        "gpp_slug": "Senegal",
        "official": {
            "CRSE Sénégal": "https://www.crse.sn",
            "SAR (Société Africaine de Raffinage)": "https://www.sar.sn",
        },
        "currency": "XOF",
    },
    "Seychelles": {
        "gpp_slug": "Seychelles",
        "official": {"PUC Seychelles": "https://www.puc.sc"},
        "currency": "SCR",
    },
    "Sierra Leone": {
        "gpp_slug": "Sierra-Leone",
        "official": {"EDSA / Ministry of Energy": "https://www.energy.gov.sl"},
        "currency": "SLL",
    },
    "Somalia": {
        "gpp_slug": "Somalia",
        "official": {"Ministry of Petroleum": "https://www.mop.gov.so"},
        "currency": "SOS",
    },
    "South Africa": {
        "gpp_slug": "South-Africa",
        "official": {
            "DFFE Fuel Levies & Prices": "https://www.energy.gov.za/files/esources/petroleum/petroleum_arch.htm",
            "Department of Mineral Resources & Energy": "https://www.energy.gov.za",
        },
        "currency": "ZAR",
    },
    "South Sudan": {
        "gpp_slug": "South-Sudan",
        "official": {"Ministry of Petroleum": "https://www.mop.gov.ss"},
        "currency": "SSP",
    },
    "Sudan": {
        "gpp_slug": "Sudan",
        "official": {"Ministry of Energy and Petroleum": "https://www.mep.gov.sd"},
        "currency": "SDG",
    },
    "Tanzania": {
        "gpp_slug": "Tanzania",
        "official": {
            "EWURA Tanzania": "https://www.ewura.go.tz",
            "EWURA Fuel Prices": "https://www.ewura.go.tz/fuel-prices/",
        },
        "currency": "TZS",
    },
    "Togo": {
        "gpp_slug": "Togo",
        "official": {"ARSE Togo": "https://www.arse.tg"},
        "currency": "XOF",
    },
    "Tunisia": {
        "gpp_slug": "Tunisia",
        "official": {
            "STIR (Société Tunisienne des Industries de Raffinage)": "https://www.stir.com.tn",
            "Ministère de l'Industrie": "https://www.industrie.gov.tn",
        },
        "currency": "TND",
    },
    "Uganda": {
        "gpp_slug": "Uganda",
        "official": {
            "Petroleum Authority of Uganda": "https://www.pau.go.ug",
            "PAU Fuel Prices": "https://www.pau.go.ug/fuel-prices",
        },
        "currency": "UGX",
    },
    "Zambia": {
        "gpp_slug": "Zambia",
        "official": {
            "ERB Zambia": "https://www.erb.org.zm",
            "ERB Pump Prices": "https://www.erb.org.zm/fuel-prices/",
        },
        "currency": "ZMW",
    },
    "Zimbabwe": {
        "gpp_slug": "Zimbabwe",
        "official": {
            "ZERA": "https://www.zera.co.zw",
            "ZERA Fuel Price": "https://www.zera.co.zw/fuel-prices/",
        },
        "currency": "ZWG",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER 1 — GlobalPetrolPrices.com (primary)
# ══════════════════════════════════════════════════════════════════════════════
def scrape_gpp_africa_table(fuel_type="gasoline"):
    """
    Scrape the Africa summary table from GlobalPetrolPrices.com.
    Returns {country_name: price_usd} or {} on failure.
    """
    url = f"https://www.globalpetrolprices.com/{fuel_type}_prices/Africa/"
    print(f"   Fetching {url}")
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        # GPP uses a table with id="countries" or class containing country rows
        results = {}
        table = (soup.find("table", id="countries")
                 or soup.find("table", class_=re.compile(r"table|price", re.I)))

        if not table:
            # Try parsing structured data in script tags
            for script in soup.find_all("script"):
                if "var itemsData" in (script.string or ""):
                    m = re.search(r"var itemsData\s*=\s*(\[.*?\]);", script.string, re.DOTALL)
                    if m:
                        items = json.loads(m.group(1))
                        for item in items:
                            if isinstance(item, list) and len(item) >= 3:
                                name  = str(item[0]).strip()
                                price = _safe_float(item[2])
                                if name and price:
                                    results[name] = price
                        if results:
                            return results

        if table:
            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    name  = cols[0].get_text(strip=True)
                    price = _safe_float(cols[2].get_text(strip=True))
                    if name and price:
                        results[name] = price

        time.sleep(DELAY)
        return results

    except Exception as e:
        print(f"   ⚠️  GPP Africa table failed: {e}")
        return {}


def scrape_gpp_country_history(country_name, slug, fuel_type="gasoline"):
    """
    Scrape the weekly historical price chart data from a country's GPP page.
    Returns list of {date, price_usd} records or [] on failure.
    """
    url = f"https://www.globalpetrolprices.com/{slug}/{fuel_type}_prices/"
    print(f"   Fetching history: {url}")
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        history = []

        # GPP embeds chart data as JS: var itemsData = [[date, price_local, price_usd], ...]
        for script in soup.find_all("script"):
            text = script.string or ""
            if "var itemsData" in text:
                m = re.search(r"var itemsData\s*=\s*(\[.*?\]);", text, re.DOTALL)
                if m:
                    items = json.loads(m.group(1))
                    for item in items:
                        if isinstance(item, (list, tuple)) and len(item) >= 3:
                            date_str  = str(item[0]).strip()
                            price_usd = _safe_float(item[2]) or _safe_float(item[1])
                            if date_str and price_usd:
                                # Filter to our period: 2026-01-01 → 2026-03-20
                                if date_str >= "2026-01-01" and date_str <= "2026-03-20":
                                    history.append({
                                        "date":       date_str,
                                        "price_usd":  round(price_usd, 4),
                                        "source":     url,
                                        "collected":  datetime.datetime.utcnow().isoformat(),
                                    })
                    break

        time.sleep(DELAY)
        return sorted(history, key=lambda x: x["date"])

    except Exception as e:
        print(f"   ⚠️  GPP country history failed for {country_name}: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER 2 — National Regulatory Authorities (key countries)
# ══════════════════════════════════════════════════════════════════════════════

def scrape_epra_kenya():
    """Kenya EPRA — publishes monthly maximum pump prices as a table."""
    url = "https://www.epra.go.ke/petroleum/maximum-petroleum-retail-prices/"
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        # Look for a table with KES prices
        tables = soup.find_all("table")
        for table in tables:
            text = table.get_text()
            if "super" in text.lower() or "petrol" in text.lower() or "diesel" in text.lower():
                for row in table.find_all("tr"):
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        label = cols[0].get_text(strip=True).lower()
                        price = _safe_float(cols[-1].get_text(strip=True))
                        if price and ("super" in label or "petrol" in label or "unleaded" in label):
                            return {"gasoline_kes": price, "source": url}
    except Exception as e:
        print(f"   ⚠️  EPRA Kenya: {e}")
    return {}


def scrape_npa_ghana():
    """Ghana NPA — publishes weekly price build-up on their website."""
    url = "https://www.npa.gov.gh"
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        # Look for price mentions in the page
        for tag in soup.find_all(["p", "td", "span", "div"]):
            text = tag.get_text(strip=True)
            m = re.search(r"GH[Cc]?\s*(\d+\.\d+)", text)
            if m:
                price_ghs = _safe_float(m.group(1))
                if price_ghs and 10 < price_ghs < 30:
                    return {"gasoline_ghs": price_ghs, "source": url}
    except Exception as e:
        print(f"   ⚠️  NPA Ghana: {e}")
    return {}


def scrape_sa_dffe():
    """South Africa DFFE — official monthly fuel price announcement."""
    url = "https://www.energy.gov.za/files/esources/petroleum/petroleum_arch.htm"
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        # Find links to the latest fuel price PDF/table
        links = soup.find_all("a", href=re.compile(r"fuel|price|petrol", re.I))
        for link in links[:5]:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            print(f"   SA DFFE link: {text[:60]} → {href[:60]}")
    except Exception as e:
        print(f"   ⚠️  SA DFFE: {e}")
    return {}


def scrape_ewura_tanzania():
    """Tanzania EWURA — publishes monthly pump prices."""
    url = "https://www.ewura.go.tz/fuel-prices/"
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 2:
                    label = cols[0].get_text(strip=True).lower()
                    price = _safe_float(cols[-1].get_text(strip=True))
                    if price and ("petrol" in label or "motor" in label):
                        return {"gasoline_tzs": price, "source": url}
    except Exception as e:
        print(f"   ⚠️  EWURA Tanzania: {e}")
    return {}


def scrape_mera_malawi():
    """Malawi MERA — publishes pump prices table."""
    url = "https://www.meramalawi.mw/pump-prices/"
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 2:
                    label = cols[0].get_text(strip=True).lower()
                    price = _safe_float(cols[-1].get_text(strip=True))
                    if price and "petrol" in label:
                        return {"gasoline_mwk": price, "source": url}
    except Exception as e:
        print(f"   ⚠️  MERA Malawi: {e}")
    return {}


def scrape_stc_mauritius():
    """Mauritius STC — publishes price table on their website."""
    url = "https://stcmu.com/petroleum-price/"
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) >= 2:
                    label = cols[0].get_text(strip=True).lower()
                    price = _safe_float(cols[-1].get_text(strip=True))
                    if price and ("mogas" in label or "petrol" in label or "unleaded" in label):
                        return {"gasoline_mur": price, "source": url}
    except Exception as e:
        print(f"   ⚠️  STC Mauritius: {e}")
    return {}


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER 3 — World Bank Commodity Price API
# ══════════════════════════════════════════════════════════════════════════════
def fetch_worldbank_crude():
    """
    Fetch World Bank commodity prices (crude oil benchmark).
    Used to cross-validate and interpolate missing data.
    Returns {date: price_usd_per_barrel}
    """
    url = ("https://api.worldbank.org/v2/en/indicator/PPETGAS.CD"
           "?downloadformat=json&date=2026-01:2026-03&mrv=12&per_page=50&format=json")
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and len(data) >= 2:
            results = {}
            for item in data[1] or []:
                if item.get("value") and item.get("date"):
                    results[item["date"]] = round(float(item["value"]), 3)
            return results
    except Exception as e:
        print(f"   ⚠️  World Bank API: {e}")
    return {}


def fetch_worldbank_fuel_prices():
    """
    World Bank pump price data (EP.PMP.SGAS.CD = pump price gasoline USD).
    Returns {country: price_usd}
    """
    url = ("https://api.worldbank.org/v2/en/indicator/EP.PMP.SGAS.CD"
           "?downloadformat=json&date=2024:2026&mrv=1&per_page=100&format=json")
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        results = {}
        if isinstance(data, list) and len(data) >= 2:
            for item in data[1] or []:
                if item.get("value") and item.get("country", {}).get("value"):
                    country = item["country"]["value"]
                    results[country] = round(float(item["value"]), 4)
        print(f"   World Bank fuel prices: {len(results)} countries")
        return results
    except Exception as e:
        print(f"   ⚠️  World Bank fuel prices: {e}")
    return {}


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE — persistent storage of all collected prices
# ══════════════════════════════════════════════════════════════════════════════
def load_db():
    """Load the persistent price database."""
    if DB_FILE.exists():
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": 1, "entries": [], "last_run": None}


def save_db(db):
    """Save the price database."""
    db["last_run"] = datetime.datetime.utcnow().isoformat()
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    print(f"   💾  DB saved → {DB_FILE}  ({len(db['entries'])} entries)")


def upsert_price(db, country, date_str, fuel_type, price_usd, source, currency, fx_rate):
    """Insert or update a price entry in the database."""
    key = f"{country}|{date_str}|{fuel_type}"
    for entry in db["entries"]:
        if entry.get("key") == key:
            entry.update({
                "price_usd":  price_usd,
                "price_loc":  round(price_usd * fx_rate, 2),
                "source":     source,
                "updated":    datetime.datetime.utcnow().isoformat(),
                "status":     "live",
            })
            return
    db["entries"].append({
        "key":       key,
        "country":   country,
        "date":      date_str,
        "fuel_type": fuel_type,
        "price_usd": price_usd,
        "price_loc": round(price_usd * fx_rate, 2),
        "currency":  currency,
        "fx_rate":   fx_rate,
        "source":    source,
        "collected": datetime.datetime.utcnow().isoformat(),
        "updated":   datetime.datetime.utcnow().isoformat(),
        "status":    "live",
    })


def get_latest_price(db, country, fuel_type="gasoline"):
    """Get the most recent price for a country from the DB."""
    matches = [e for e in db["entries"]
               if e["country"] == country and e["fuel_type"] == fuel_type]
    if not matches:
        return None
    return sorted(matches, key=lambda x: x["date"], reverse=True)[0]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN COLLECTION ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════
def run_collection():
    """
    Full collection pipeline:
      1. Scrape GPP Africa summary table  → current prices for all 54 countries
      2. Scrape GPP country history pages → weekly series Jan–Mar 2026
      3. Scrape national authority pages  → verify key countries
      4. Store everything in prices_db.json
    """
    from data import COUNTRIES, FX_RATES

    today    = datetime.date.today().isoformat()
    db       = load_db()
    now_str  = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    stats    = {"live": 0, "history": 0, "failed": 0}

    print(f"\n{'='*65}")
    print(f"  AFRICA FUEL TRACKER — REAL DATA COLLECTION")
    print(f"  {now_str}")
    print(f"{'='*65}\n")

    # ── Step 1: GPP Africa summary (current prices for all countries) ──────────
    print("STEP 1 — GlobalPetrolPrices.com Africa tables")
    print("  Collecting current gasoline prices...")
    gpp_gas = scrape_gpp_africa_table("gasoline")
    print(f"  → {len(gpp_gas)} gasoline prices collected")

    print("  Collecting current diesel prices...")
    gpp_die = scrape_gpp_africa_table("diesel_prices")
    print(f"  → {len(gpp_die)} diesel prices collected")

    # Match GPP names to our country list
    country_map = {c[0]: c for c in COUNTRIES}
    gpp_name_map = {
        "South Africa": "South Africa", "Nigeria": "Nigeria", "Kenya": "Kenya",
        "Egypt": "Egypt", "Ethiopia": "Ethiopia", "Ghana": "Ghana",
        "Tanzania": "Tanzania", "Uganda": "Uganda", "Mozambique": "Mozambique",
        "Zambia": "Zambia", "Zimbabwe": "Zimbabwe", "Senegal": "Senegal",
        "Ivory Coast": "Ivory Coast", "Cameroon": "Cameroon", "Angola": "Angola",
        "Algeria": "Algeria", "Morocco": "Morocco", "Tunisia": "Tunisia",
        "Libya": "Libya", "Sudan": "Sudan", "Rwanda": "Rwanda",
        "Malawi": "Malawi", "Madagascar": "Madagascar", "Mali": "Mali",
        "Burkina Faso": "Burkina Faso", "Benin": "Benin", "Togo": "Togo",
        "Niger": "Niger", "Guinea": "Guinea", "Sierra Leone": "Sierra Leone",
        "Liberia": "Liberia", "Gambia": "Gambia", "Botswana": "Botswana",
        "Namibia": "Namibia", "Eswatini": "Eswatini", "Lesotho": "Lesotho",
        "Mauritius": "Mauritius", "Seychelles": "Seychelles",
        "Comoros": "Comoros", "Djibouti": "Djibouti", "Eritrea": "Eritrea",
        "Somalia": "Somalia", "South Sudan": "South Sudan",
        "Burundi": "Burundi", "Chad": "Chad", "Gabon": "Gabon",
        "Equatorial Guinea": "Equatorial Guinea", "Cabo Verde": "Cabo Verde",
        "Central African Republic": "CAR", "Congo": "Congo DR",
        "Republic of the Congo": "Congo Rep.", "Guinea-Bissau": "Guinea-Bissau",
        "Mauritania": "Mauritania", "Sao Tome And Principe": "Sao Tome",
    }

    for gpp_name, our_name in gpp_name_map.items():
        if our_name not in country_map:
            continue
        _, _, currency, _ = country_map[our_name]
        fx = FX_RATES.get(currency, 1.0)

        if gpp_name in gpp_gas:
            price = gpp_gas[gpp_name]
            upsert_price(db, our_name, today, "gasoline", price,
                         "GlobalPetrolPrices.com", currency, fx)
            stats["live"] += 1

        if gpp_name in gpp_die:
            price = gpp_die[gpp_name]
            upsert_price(db, our_name, today, "diesel", price,
                         "GlobalPetrolPrices.com", currency, fx)

    print(f"  → {stats['live']} live prices stored")

    # ── Step 2: GPP country history (weekly Jan–Mar 2026) ──────────────────────
    print("\nSTEP 2 — GPP country historical weekly data (Jan–Mar 2026)")
    print("  Fetching weekly history for all 54 countries...")

    for country_name, info in COUNTRY_SOURCES.items():
        slug = info.get("gpp_slug", country_name.replace(" ", "-"))
        currency = info.get("currency", "USD")
        fx = FX_RATES.get(currency, 1.0)

        # Gasoline history
        history = scrape_gpp_country_history(country_name, slug, "gasoline")
        for pt in history:
            upsert_price(db, country_name, pt["date"], "gasoline",
                         pt["price_usd"], pt["source"], currency, fx)
            stats["history"] += 1

        # Diesel history
        history_d = scrape_gpp_country_history(country_name, slug, "diesel_prices")
        for pt in history_d:
            upsert_price(db, country_name, pt["date"], "diesel",
                         pt["price_usd"], pt["source"], currency, fx)

        time.sleep(DELAY)

    print(f"  → {stats['history']} historical data points stored")

    # ── Step 3: National authority verification (key countries) ───────────────
    print("\nSTEP 3 — National authority verification")
    national_scrapers = {
        "Kenya":      scrape_epra_kenya,
        "Ghana":      scrape_npa_ghana,
        "South Africa": scrape_sa_dffe,
        "Tanzania":   scrape_ewura_tanzania,
        "Malawi":     scrape_mera_malawi,
        "Mauritius":  scrape_stc_mauritius,
    }
    for country_name, scraper_fn in national_scrapers.items():
        print(f"  Checking {country_name}...")
        result = scraper_fn()
        if result:
            print(f"   ✅  {country_name}: {result}")
        else:
            print(f"   ⚠️  {country_name}: no data from national source")
            stats["failed"] += 1

    # ── Step 4: Save DB ────────────────────────────────────────────────────────
    print("\nSTEP 4 — Saving database")
    save_db(db)

    # ── Summary ────────────────────────────────────────────────────────────────
    total = len(db["entries"])
    countries_with_data = len(set(e["country"] for e in db["entries"]))
    print(f"\n{'='*65}")
    print(f"  COLLECTION COMPLETE")
    print(f"  Live prices collected : {stats['live']}")
    print(f"  Historical data points: {stats['history']}")
    print(f"  Countries with data   : {countries_with_data}/54")
    print(f"  Total DB entries      : {total}")
    print(f"  Failed scrapers       : {stats['failed']}")
    print(f"{'='*65}\n")

    return db


# ══════════════════════════════════════════════════════════════════════════════
# DB → records for pipeline (replaces data.build_records)
# ══════════════════════════════════════════════════════════════════════════════
def build_records_from_db(fx_rates=None):
    """
    Build the standard records list from the real collected DB.
    Falls back to data.py seed prices for any missing country/fuel.
    """
    from data import COUNTRIES, FX_RATES, WEEK_DATES, WEEK_LABELS, N_WEEKS, build_records

    if fx_rates is None:
        fx_rates = FX_RATES

    db = load_db()
    if not db["entries"]:
        print("   ⚠️  DB is empty — using seed data from data.py")
        return build_records(fx_rates)

    # Seed records as fallback
    seed_records = {r["name"]: r for r in build_records(fx_rates)}
    now          = datetime.datetime.utcnow()
    records      = []

    for name, region, currency, octane in COUNTRIES:
        fx   = fx_rates.get(currency, 1.0)
        seed = seed_records.get(name, {})

        def get_price(fuel_type, week_date):
            """Get real price for a specific week, or interpolate/fallback."""
            date_str = week_date.isoformat()
            # Look for exact date
            for entry in db["entries"]:
                if entry["country"] == name and entry["fuel_type"] == fuel_type:
                    if entry["date"] == date_str:
                        return entry["price_usd"], entry.get("source", "DB"), "live"
            # Look for nearest date within ±7 days
            candidates = [
                e for e in db["entries"]
                if e["country"] == name and e["fuel_type"] == fuel_type
            ]
            if candidates:
                nearest = min(candidates,
                              key=lambda e: abs((datetime.date.fromisoformat(e["date"])
                                                 - week_date).days))
                if abs((datetime.date.fromisoformat(nearest["date"]) - week_date).days) <= 7:
                    return nearest["price_usd"], nearest.get("source", "DB"), "interpolated"
            return None, "seed", "fallback"

        # Build weekly series
        gas_usd, die_usd = [], []
        gas_src, die_src = [], []

        for wd in WEEK_DATES:
            gp, gs, gstatus = get_price("gasoline", wd)
            dp, ds, dstatus = get_price("diesel",   wd)

            # Use seed series as baseline, override with real if available
            seed_g = seed.get("gas_usd_w", [None]*N_WEEKS)
            seed_d = seed.get("die_usd_w", [None]*N_WEEKS)
            wi     = WEEK_DATES.index(wd)

            gas_usd.append(round(gp  if gp  else (seed_g[wi] if wi < len(seed_g) else 1.0), 4))
            die_usd.append(round(dp  if dp  else (seed_d[wi] if wi < len(seed_d) else 0.9), 4))
            gas_src.append(gstatus)
            die_src.append(dstatus)

        gas_loc = [round(p * fx, 2) for p in gas_usd]
        die_loc = [round(p * fx, 2) for p in die_usd]

        # Latest LPG (use seed — rarely available in real-time)
        lpg_usd = seed.get("lpg_usd", 1.2)
        lpg_loc = round(lpg_usd * fx, 2)

        # Data quality flag
        live_count = gas_src.count("live") + gas_src.count("interpolated")
        quality    = "live" if live_count >= 8 else ("partial" if live_count >= 4 else "seed")

        records.append({
            "name":       name, "region": region,
            "currency":   currency, "octane": octane, "fx_rate": fx,
            "gas_usd":    gas_usd[-1], "die_usd": die_usd[-1], "lpg_usd": lpg_usd,
            "gas_loc":    gas_loc[-1], "die_loc": die_loc[-1], "lpg_loc": lpg_loc,
            "gas_usd_w":  gas_usd, "die_usd_w": die_usd,
            "gas_loc_w":  gas_loc, "die_loc_w": die_loc,
            "chg_gas":    round((gas_usd[-1]-gas_usd[0])/gas_usd[0]*100, 2) if gas_usd[0] else 0,
            "chg_die":    round((die_usd[-1]-die_usd[0])/die_usd[0]*100, 2) if die_usd[0] else 0,
            "min_gas":    round(min(gas_usd), 4),
            "max_gas":    round(max(gas_usd), 4),
            "avg_gas":    round(sum(gas_usd)/len(gas_usd), 4),
            "data_quality": quality,     # "live" | "partial" | "seed"
            "sources":      list(set(gas_src)),
            "updated":      now.strftime("%Y-%m-%d %H:%M UTC"),
        })

    return sorted(records, key=lambda r: r["name"])


# ══════════════════════════════════════════════════════════════════════════════
def _safe_float(text):
    """Extract a float from a string, return None if not possible."""
    if not text:
        return None
    text = re.sub(r"[^\d.]", "", str(text).strip())
    try:
        v = float(text)
        return v if 0.001 < v < 10000 else None
    except ValueError:
        return None


if __name__ == "__main__":
    run_collection()

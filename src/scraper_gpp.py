"""
scraper_gpp.py — Africa Fuel Tracker · GPP Scraper (Playwright)
================================================================
Scrape GlobalPetrolPrices.com pour tous les pays africains disponibles.

Architecture :
  ┌─────────────────────────────────────────────────────────┐
  │  GPP Africa list (42 pays)                              │
  │  https://www.globalpetrolprices.com/{slug}/gasoline_prices/ │
  │  https://www.globalpetrolprices.com/{slug}/diesel_prices/   │
  │                                                         │
  │  Chaque page contient :                                 │
  │   • Prix actuel local + USD                             │
  │   • Série historique via JavaScript itemsData           │
  │     [ ["2026-01-05", local_price, usd_price], ... ]    │
  │   • Indicateur * = hebdomadaire vs mensuel              │
  └─────────────────────────────────────────────────────────┘

Fallback (12 pays absents de GPP) :
  Chad, Comoros, Congo Rep., Djibouti, Equatorial Guinea,
  Eritrea, Gambia, Guinea-Bissau, Mauritania, Sao Tome,
  Somalia, South Sudan
  → Gardés depuis data.py (données calibrées)
"""

import asyncio, json, re, datetime, time
from pathlib import Path

# ── Mapping GPP slug → nom interne ────────────────────────────────────────────
GPP_AFRICA = {
    "Algeria":                          "Algeria",
    "Angola":                           "Angola",
    "Benin":                            "Benin",
    "Botswana":                         "Botswana",
    "Burkina-Faso":                     "Burkina Faso",
    "Burundi":                          "Burundi",
    "Cameroon":                         "Cameroon",
    "Cape-Verde":                       "Cabo Verde",
    "Central-African-Republic":         "CAR",
    "Democratic-Republic-of-the-Congo": "Congo DR",
    "Egypt":                            "Egypt",
    "Ethiopia":                         "Ethiopia",
    "Gabon":                            "Gabon",
    "Ghana":                            "Ghana",
    "Guinea":                           "Guinea",
    "Ivory-Coast":                      "Ivory Coast",
    "Kenya":                            "Kenya",
    "Lesotho":                          "Lesotho",
    "Liberia":                          "Liberia",
    "Libya":                            "Libya",
    "Madagascar":                       "Madagascar",
    "Malawi":                           "Malawi",
    "Mali":                             "Mali",
    "Mauritius":                        "Mauritius",
    "Morocco":                          "Morocco",
    "Mozambique":                       "Mozambique",
    "Namibia":                          "Namibia",
    "Niger":                            "Niger",
    "Nigeria":                          "Nigeria",
    "Rwanda":                           "Rwanda",
    "Senegal":                          "Senegal",
    "Seychelles":                       "Seychelles",
    "Sierra-Leone":                     "Sierra Leone",
    "South-Africa":                     "South Africa",
    "Sudan":                            "Sudan",
    "Swaziland":                        "Eswatini",
    "Tanzania":                         "Tanzania",
    "Togo":                             "Togo",
    "Tunisia":                          "Tunisia",
    "Uganda":                           "Uganda",
    "Zambia":                           "Zambia",
    "Zimbabwe":                         "Zimbabwe",
}

GPP_BASE     = "https://www.globalpetrolprices.com"
PERIOD_FROM  = "2026-01-01"
PERIOD_TO    = "2026-03-23"   # today (updated dynamically)
DELAY_MS     = 1200           # délai poli entre requêtes (ms)
TIMEOUT_MS   = 25000


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER PLAYWRIGHT — async
# ══════════════════════════════════════════════════════════════════════════════

async def _extract_gpp_page(page, url, country_name, fuel_type):
    """
    Scrape une page GPP pays/carburant.
    Retourne:
        current_price_usd  : float | None
        current_price_local: float | None
        local_currency     : str
        history            : [{date, price_usd, price_local}]
        is_regulated       : bool   (ligne plate = marché régulé)
        last_updated       : str
    """
    result = {
        "current_usd":   None,
        "current_local": None,
        "currency":      "",
        "history":       [],
        "is_regulated":  False,
        "last_updated":  "",
        "source":        url,
    }

    try:
        await page.goto(url, wait_until="networkidle", timeout=TIMEOUT_MS)
        await page.wait_for_timeout(1500)

        # ── 1. Extraire itemsData depuis le contexte JS ─────────────────────
        items = await page.evaluate("""
            () => {
                // Try direct variable
                if (typeof itemsData !== 'undefined') return itemsData;
                if (typeof window.itemsData !== 'undefined') return window.itemsData;
                // Try to parse from script tags
                const scripts = document.querySelectorAll('script');
                for (const s of scripts) {
                    const t = s.textContent || '';
                    const m = t.match(/var\\s+itemsData\\s*=\\s*(\\[[\\s\\S]*?\\]);/);
                    if (m) {
                        try { return JSON.parse(m[1]); } catch(e) {}
                    }
                    // Try without var
                    const m2 = t.match(/itemsData\\s*=\\s*(\\[[\\s\\S]*?\\]);/);
                    if (m2) {
                        try { return JSON.parse(m2[1]); } catch(e) {}
                    }
                }
                return null;
            }
        """)

        if items:
            history = []
            usd_values = []
            for item in items:
                if not isinstance(item, (list, tuple)) or len(item) < 2:
                    continue
                date_str = str(item[0]).strip()
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                    continue
                # item = [date, local_price, usd_price]
                local = _safe_float(item[1]) if len(item) > 1 else None
                usd   = _safe_float(item[2]) if len(item) > 2 else None
                if not usd and local:
                    usd = local  # fallback
                if usd:
                    usd_values.append(usd)
                # Filter to our period
                if PERIOD_FROM <= date_str <= PERIOD_TO and usd:
                    # Period-specific FX rate: derived from GPP data itself
                    # local_price / usd_price = exact exchange rate at that date
                    fx_period = round(local / usd, 4) if local and usd and usd > 0 else None
                    history.append({
                        "date":        date_str,
                        "price_usd":   round(usd, 4),
                        "price_local": round(local, 3) if local else None,
                        "fx_period":   fx_period,   # exact rate at this date
                    })

            result["history"] = sorted(history, key=lambda x: x["date"])

            # Current price = most recent in history or last itemsData entry
            if history:
                result["current_usd"] = history[-1]["price_usd"]
                result["current_local"] = history[-1].get("price_local")

            # Detect regulated market (flat line = same price repeated)
            if len(usd_values) >= 4:
                unique = set(round(v, 2) for v in usd_values[-8:])
                result["is_regulated"] = len(unique) <= 2

        # ── 2. Extract current price from HTML if not found in JS ───────────
        if not result["current_usd"]:
            # Look for price pattern in page text
            content = await page.content()
            # GPP format: "ZAR 19.89 per liter or USD 1.19 per liter"
            m = re.search(
                r'(?:USD|U\.S\.\s*Dollar)\s+([\d.]+)\s*per\s*li(?:t|t?re)',
                content, re.I
            )
            if m:
                result["current_usd"] = _safe_float(m.group(1))

        # ── 3. Extract last updated date ────────────────────────────────────
        content = await page.content()
        m = re.search(r'updated\s+(?:on\s+)?(\d{2}-\w{3}-\d{4})', content, re.I)
        if m:
            result["last_updated"] = m.group(1)

        # ── 4. Extract currency from page title ─────────────────────────────
        m = re.search(r'([A-Z]{3})\s+[\d.,]+\s+per\s+li', content, re.I)
        if m:
            result["currency"] = m.group(1).upper()

    except Exception as e:
        print(f"     ⚠️  {country_name} {fuel_type}: {type(e).__name__}: {str(e)[:60]}")

    return result


async def scrape_all_africa(period_to=None):
    """
    Scrape tous les pays africains GPP.
    Retourne dict: {country_name: {gas: {...}, diesel: {...}}}
    """
    if period_to:
        global PERIOD_TO
        PERIOD_TO = period_to

    from playwright.async_api import async_playwright

    results = {}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", "--disable-setuid-sandbox",
                "--disable-dev-shm-usage", "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            },
        )
        # Anti-detection
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
            window.chrome = {runtime: {}};
        """)

        page = await context.new_page()

        total = len(GPP_AFRICA)
        for i, (slug, country_name) in enumerate(GPP_AFRICA.items()):
            print(f"  [{i+1:02d}/{total}] {country_name} ({slug})...")
            results[country_name] = {"gas": {}, "diesel": {}}

            for fuel_type, url_seg in [("gas", "gasoline_prices"), ("diesel", "diesel_prices")]:
                url  = f"{GPP_BASE}/{slug}/{url_seg}/"
                data = await _extract_gpp_page(page, url, country_name, fuel_type)
                results[country_name][fuel_type] = data

                n_hist = len(data["history"])
                curr   = data["current_usd"]
                reg    = "📋 regulated" if data["is_regulated"] else "📈 free market"
                if curr:
                    print(f"     ✅ {fuel_type}: ${curr:.3f}/L | {n_hist} history pts | {reg}")
                else:
                    print(f"     ⚠️  {fuel_type}: no price found")

                await page.wait_for_timeout(DELAY_MS)

        await context.close()
        await browser.close()

    # Summary
    countries_gas    = sum(1 for v in results.values() if v["gas"].get("current_usd"))
    countries_die    = sum(1 for v in results.values() if v["diesel"].get("current_usd"))
    history_pts      = sum(len(v["gas"].get("history", [])) for v in results.values())
    regulated_count  = sum(1 for v in results.values() if v["gas"].get("is_regulated"))

    print(f"\n{'='*60}")
    print(f"  GPP SCRAPING COMPLETE")
    print(f"  Gas current prices   : {countries_gas}/{total}")
    print(f"  Diesel current prices: {countries_die}/{total}")
    print(f"  History data points  : {history_pts}")
    print(f"  Regulated markets    : {regulated_count}")
    print(f"  Free markets         : {total - regulated_count}")
    print(f"{'='*60}")

    return results


# ══════════════════════════════════════════════════════════════════════════════
# INTERFACE SYNCHRONE
# ══════════════════════════════════════════════════════════════════════════════

def run_gpp_scraper(period_to=None):
    """Point d'entrée synchrone. Retourne les données ou {} en cas d'erreur."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  ❌ playwright not installed")
        return {}
    try:
        return asyncio.run(scrape_all_africa(period_to))
    except Exception as e:
        print(f"  ❌ GPP scraper error: {e}")
        import traceback; traceback.print_exc()
        return {}


def _safe_float(val):
    if val is None: return None
    try:
        v = float(re.sub(r"[^\d.]", "", str(val).strip()))
        return v if v > 0 else None
    except: return None


# ══════════════════════════════════════════════════════════════════════════════
# INTÉGRATION DB — GPP results → prices_db.json
# ══════════════════════════════════════════════════════════════════════════════

def save_gpp_to_db(gpp_results, db, fx_rates, country_defs):
    """
    Intègre les résultats GPP dans la DB.
    Écrase les entrées existantes si src_code >= A.
    """
    today    = datetime.date.today().isoformat()
    added    = 0
    updated  = 0
    order    = {"D":5, "C":4, "B":3, "A":2, "E":1}
    src_code = "A"  # GPP = source A

    for country_name, data in gpp_results.items():
        if country_name not in country_defs:
            continue
        _, _, currency, _ = country_defs[country_name]
        fx = fx_rates.get(currency, 1.0)

        for fuel_type in ["gas", "diesel"]:
            fuel_db = "gasoline" if fuel_type == "gas" else "diesel"
            d = data.get(fuel_type, {})

            # Current price for today
            if d.get("current_usd"):
                key = f"{country_name}|{today}|{fuel_db}"
                entry = {
                    "key":       key,
                    "country":   country_name,
                    "date":      today,
                    "fuel_type": fuel_db,
                    "price_usd": round(d["current_usd"], 4),
                    "price_loc": round(d["current_usd"] * fx, 2),
                    "currency":  currency,
                    "fx_rate":   fx,
                    "source":    f"GlobalPetrolPrices.com ({d.get('last_updated','today')})",
                    "src_code":  src_code,
                    "is_regulated": d.get("is_regulated", False),
                    "updated":   datetime.datetime.utcnow().isoformat(),
                    "status":    "live",
                }
                # Upsert
                found = False
                for i, e in enumerate(db["entries"]):
                    if e.get("key") == key:
                        if order.get(src_code,0) >= order.get(e.get("src_code","E"),0):
                            db["entries"][i] = {**e, **entry}
                            updated += 1
                        found = True
                        break
                if not found:
                    entry["collected"] = entry["updated"]
                    db["entries"].append(entry)
                    added += 1

            # Historical points (Jan-Mar 2026)
            for pt in d.get("history", []):
                date_str = pt["date"]
                key      = f"{country_name}|{date_str}|{fuel_db}"
                price    = pt["price_usd"]
                # Use period-specific FX rate if available from GPP data
                fx_pt    = pt.get("fx_period") or fx
                entry_h  = {
                    "key":       key,
                    "country":   country_name,
                    "date":      date_str,
                    "fuel_type": fuel_db,
                    "price_usd": round(price, 4),
                    "price_loc": round(price * fx_pt, 2),   # period FX
                    "currency":  currency,
                    "fx_rate":   round(fx_pt, 4),            # period FX stored
                    "source":    f"GlobalPetrolPrices.com (history)",
                    "src_code":  src_code,
                    "updated":   datetime.datetime.utcnow().isoformat(),
                    "status":    "live",
                }
                found = False
                for i, e in enumerate(db["entries"]):
                    if e.get("key") == key:
                        if order.get(src_code,0) >= order.get(e.get("src_code","E"),0):
                            db["entries"][i] = {**e, **entry_h}
                            updated += 1
                        found = True
                        break
                if not found:
                    entry_h["collected"] = entry_h["updated"]
                    db["entries"].append(entry_h)
                    added += 1

    print(f"   DB: +{added} new entries, {updated} updated (src=A GPP)")
    return added + updated


if __name__ == "__main__":
    # Test run
    print("Starting GPP scraper for all African countries...")
    print(f"Target: {len(GPP_AFRICA)} countries × 2 fuels × history Jan-Mar 2026")
    results = run_gpp_scraper()
    if results:
        # Save to file for inspection
        out = Path("/home/claude/gh_project/data/gpp_raw.json")
        with open(out, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nRaw results saved to: {out}")

"""
scraper_playwright.py — Africa Fuel Tracker · Playwright Scraper
================================================================
Utilise Playwright (navigateur headless Chromium) pour scraper
GlobalPetrolPrices.com — contourne le JS dynamique et Cloudflare.

Collecte:
  1. Prix actuels (tableau Afrique)  → /gasoline_prices/Africa/
  2. Historique Jan–Mar 2026          → /COUNTRY/gasoline_prices/ (× 54)

Playwright simule un vrai navigateur → pas de blocage Cloudflare.
"""

import asyncio, json, re, time, datetime
from pathlib import Path

# ── Constantes ────────────────────────────────────────────────────────────────
GPP_BASE    = "https://www.globalpetrolprices.com"
PERIOD_FROM = "2026-01-01"
PERIOD_TO   = "2026-03-21"
DELAY_MS    = 1500     # délai poli entre pages (ms)
TIMEOUT_MS  = 30000    # timeout navigation (ms)


# ══════════════════════════════════════════════════════════════════════════════
# SCRAPER PRINCIPAL — async
# ══════════════════════════════════════════════════════════════════════════════

async def scrape_all(country_slugs: dict) -> dict:
    """
    Scrape GPP pour tous les pays.
    country_slugs = {country_name: gpp_slug}
    Retourne: {country_name: {"current_gas": float, "current_die": float,
                               "history_gas": [{date, price_usd}],
                               "history_die": [{date, price_usd}]}}
    """
    from playwright.async_api import async_playwright, TimeoutError as PWTimeout

    results = {}

    async with async_playwright() as pw:
        # Lance Chromium en mode headless avec configuration anti-détection
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-blink-features=AutomationControlled",
            ]
        )

        # Contexte navigateur avec configuration réaliste
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "DNT": "1",
            },
        )

        # Masque les propriétés d'automatisation
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            window.chrome = {runtime: {}};
        """)

        page = await context.new_page()

        # ── Étape 1 : Tableau Afrique (prix actuels) ──────────────────────
        print("  [Playwright] Étape 1 — Tableau Afrique (prix actuels)")
        for fuel_type, url_path in [
            ("gasoline", "/gasoline_prices/Africa/"),
            ("diesel",   "/diesel_prices/Africa/"),
        ]:
            url = GPP_BASE + url_path
            try:
                print(f"    → {url}")
                await page.goto(url, wait_until="networkidle", timeout=TIMEOUT_MS)
                await page.wait_for_timeout(2000)  # laisse le JS s'exécuter

                # Stratégie 1 : Extrait itemsData depuis le JS de la page
                items = await page.evaluate("""
                    () => {
                        if (typeof itemsData !== 'undefined') return itemsData;
                        if (typeof window.itemsData !== 'undefined') return window.itemsData;
                        return null;
                    }
                """)

                if items:
                    print(f"    ✅ itemsData trouvé: {len(items)} pays")
                    for item in items:
                        if isinstance(item, list) and len(item) >= 3:
                            name = str(item[0]).strip()
                            usd  = _safe_float(item[2]) or _safe_float(item[1])
                            if name and usd and 0.001 < usd < 20:
                                if name not in results:
                                    results[name] = {}
                                results[name][f"current_{fuel_type[:3]}"] = usd
                    continue

                # Stratégie 2 : Parse le tableau HTML
                rows = await page.query_selector_all("table#countries tr, table.countryList tr")
                if not rows:
                    rows = await page.query_selector_all("tr")

                parsed = 0
                for row in rows:
                    try:
                        cells = await row.query_selector_all("td")
                        if len(cells) < 2:
                            continue
                        name_el = await cells[0].query_selector("a")
                        if not name_el:
                            continue
                        name = (await name_el.inner_text()).strip()
                        # Cherche le prix USD dans les cellules
                        usd = None
                        for i in range(1, min(6, len(cells))):
                            val = await cells[i].get_attribute("data-value") or \
                                  await cells[i].inner_text()
                            v = _safe_float(val)
                            if v and 0.001 < v < 20:
                                usd = v
                                break
                        if name and usd:
                            if name not in results:
                                results[name] = {}
                            results[name][f"current_{fuel_type[:3]}"] = usd
                            parsed += 1
                    except Exception:
                        continue

                print(f"    {'✅' if parsed > 0 else '⚠️ '} HTML table: {parsed} pays parsés")

            except PWTimeout:
                print(f"    ⏱️  Timeout sur {url}")
            except Exception as e:
                print(f"    ❌  Erreur: {e}")

            await page.wait_for_timeout(DELAY_MS)

        # ── Étape 2 : Historique par pays (Jan–Mar 2026) ──────────────────
        print(f"\n  [Playwright] Étape 2 — Historique par pays ({len(country_slugs)} pays)")

        for country_name, slug in country_slugs.items():
            if country_name not in results:
                results[country_name] = {}
            results[country_name]["history_gas"] = []
            results[country_name]["history_die"] = []

            for fuel_type, url_path in [
                ("gas", f"/{slug}/gasoline_prices/"),
                ("die", f"/{slug}/diesel_prices/"),
            ]:
                url = GPP_BASE + url_path
                try:
                    await page.goto(url, wait_until="networkidle", timeout=TIMEOUT_MS)
                    await page.wait_for_timeout(1500)

                    # Extrait itemsData depuis le contexte JS de la page
                    items = await page.evaluate("""
                        () => {
                            if (typeof itemsData !== 'undefined') return itemsData;
                            if (typeof window.itemsData !== 'undefined') return window.itemsData;
                            // Essaie de trouver dans les scripts
                            const scripts = document.querySelectorAll('script');
                            for (const s of scripts) {
                                const m = s.textContent.match(/itemsData\s*=\s*(\[[\s\S]*?\]);/);
                                if (m) {
                                    try { return JSON.parse(m[1]); } catch(e) {}
                                }
                            }
                            return null;
                        }
                    """)

                    if not items:
                        # Fallback: extrait via regex sur le HTML source
                        content = await page.content()
                        m = re.search(r'var\s+itemsData\s*=\s*(\[[\s\S]*?\]);', content)
                        if m:
                            try:
                                items = json.loads(m.group(1))
                            except json.JSONDecodeError:
                                pass

                    if items:
                        history = []
                        for item in items:
                            if not isinstance(item, (list, tuple)) or len(item) < 2:
                                continue
                            date_str = str(item[0]).strip()
                            # Vérifie format date YYYY-MM-DD
                            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                                continue
                            # Filtre période Jan–Mar 2026
                            if PERIOD_FROM <= date_str <= PERIOD_TO:
                                usd = _safe_float(item[2]) if len(item) > 2 else None
                                usd = usd or _safe_float(item[1])
                                if usd and 0.001 < usd < 20:
                                    history.append({
                                        "date":      date_str,
                                        "price_usd": round(usd, 4),
                                        "source":    url,
                                        "collected": datetime.datetime.utcnow().isoformat(),
                                    })

                        results[country_name][f"history_{fuel_type}"] = \
                            sorted(history, key=lambda x: x["date"])

                        if history:
                            print(f"    ✅ {country_name:22s} {fuel_type}: {len(history)} pts "
                                  f"({history[0]['date']} → {history[-1]['date']}) "
                                  f"| ${history[0]['price_usd']:.3f} → ${history[-1]['price_usd']:.3f}")
                        else:
                            print(f"    ⚠️  {country_name:22s} {fuel_type}: page OK mais 0 pts dans période")
                    else:
                        print(f"    ❌ {country_name:22s} {fuel_type}: itemsData non trouvé")

                except PWTimeout:
                    print(f"    ⏱️  {country_name} {fuel_type}: timeout")
                except Exception as e:
                    print(f"    ❌ {country_name} {fuel_type}: {e}")

                await page.wait_for_timeout(DELAY_MS)

        await context.close()
        await browser.close()

    return results


# ══════════════════════════════════════════════════════════════════════════════
# INTERFACE SYNCHRONE (appelée depuis collector.py)
# ══════════════════════════════════════════════════════════════════════════════

def run_playwright_scraper(country_slugs: dict) -> dict:
    """
    Point d'entrée synchrone.
    Retourne les données scrapées ou {} en cas d'erreur.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  ❌ Playwright non installé — pip install playwright")
        return {}

    try:
        print("  🎭 Démarrage Playwright (Chromium headless)...")
        data = asyncio.run(scrape_all(country_slugs))
        n_countries = sum(1 for v in data.values() if v.get("history_gas"))
        n_points    = sum(len(v.get("history_gas", [])) for v in data.values())
        print(f"  ✅ Playwright terminé: {n_countries} pays, {n_points} points historiques")
        return data
    except Exception as e:
        print(f"  ❌ Playwright erreur: {e}")
        import traceback; traceback.print_exc()
        return {}


def _safe_float(val):
    if val is None:
        return None
    try:
        v = float(re.sub(r"[^\d.]", "", str(val).strip()))
        return v if v > 0 else None
    except (ValueError, TypeError):
        return None


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Test rapide avec 3 pays
    test_slugs = {
        "Nigeria":      "Nigeria",
        "South Africa": "South-Africa",
        "Kenya":        "Kenya",
        "Egypt":        "Egypt",
        "Morocco":      "Morocco",
    }
    print("Test Playwright scraper (5 pays)...")
    data = run_playwright_scraper(test_slugs)
    print("\nRésultats:")
    for country, info in data.items():
        gas = info.get("history_gas", [])
        print(f"  {country:20s} current=${info.get('current_gas','?')} "
              f"history={len(gas)} pts")

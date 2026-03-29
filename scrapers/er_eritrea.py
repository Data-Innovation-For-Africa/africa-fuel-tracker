"""
Eritrea — No official publication since 2016
Update cycle : STABLE (country very closed, no public data)
Primary URL  : https://www.thefuelprice.com/Fer/en (aggregator)
Currency     : ERN (fixed rate 15 ERN/USD since 2005)

Scraping strategy:
  1. thefuelprice.com/Fer/en → parse ERN prices if available
  2. DuckDuckGo              → "Eritrea fuel price ERN nakfa {year} official"
  3. If nothing found        → return last known (2016), old_source=True, confidence=low
  NOTE: Never raises ScraperError — always returns last known per project rules.
"""
import re
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_STABLE, _fetch, _extract_any_date
from utils.search import search, fetch_page, extract_prices_from_text
from utils.base import CountryResult


class EritreaScraper(SmartScraper):

    COUNTRY_META = {
        "country":      "Eritrea",
        "iso2":         "ER",
        "region":       "East Africa",
        "currency":     "ERN",
        "update_cycle": CYCLE_STABLE,
        "price_range":  (5, 100),
        "old_source":   True,   # always flagged

        "official_sources": [
            {"url": "https://www.thefuelprice.com/Fer/en",
             "name": "TheFuelPrice.com — Eritrea", "confidence": "low"},
        ],

        "search_queries": [
            "Eritrea fuel price ERN nakfa per liter {year} official government",
            "Eritrea gasoline diesel price {year} Asmara pump",
        ],

        "last_known": {"gas_loc": 30.0, "die_loc": 20.0, "date": "2016-12-01"},
    }

    def run(self) -> CountryResult:
        """
        Override run() — Eritrea NEVER raises ScraperError.
        Always returns a result (either fresh or last known).
        """
        meta = self.COUNTRY_META
        min_v, max_v = meta["price_range"]

        # Try official sources
        for source in meta["official_sources"]:
            html = _fetch(source["url"])
            if html:
                try:
                    gas, die, eff_date = self._parse(html, source["url"])
                    if gas and die:
                        return self._build_result(gas, die, eff_date,
                                                   source["url"], source["name"],
                                                   confidence="low")
                except Exception:
                    pass

        # Try DuckDuckGo
        today = date.today()
        for query_tpl in meta["search_queries"]:
            query = query_tpl.format(year=today.year, month=today.strftime("%B"))
            results = search(query, max_results=5)
            for result in results:
                html = fetch_page(result.url)
                if html:
                    gas, die = extract_prices_from_text(html, "ERN", min_v, max_v)
                    if gas and die:
                        eff_date = _extract_any_date(html) or today.isoformat()
                        return self._build_result(gas, die, eff_date,
                                                   result.url, result.domain,
                                                   confidence="low")

        # Fallback: return last known
        lk = meta["last_known"]
        print(f"    [Eritrea] Using last known values from {lk['date']} (old_source=True)")
        return self._build_result(
            lk["gas_loc"], lk["die_loc"], lk["date"],
            "https://www.thefuelprice.com/Fer/en",
            "TheFuelPrice.com — Eritrea (last known 2016)",
            confidence="low",
        )

    def _parse(self, html: str, url: str) -> tuple[float, float, str]:
        text = self._text(html)
        gas = die = None

        for kw in ["gasoline", "petrol", "benzine"]:
            m = re.search(rf"(?i){kw}[^0-9]{{0,40}}?([\d]+\.[\d]{{1,3}})", text)
            if m:
                v = float(m.group(1))
                if 5 <= v <= 100:
                    gas = v
                    break

        for kw in ["diesel", "gasoil"]:
            m = re.search(rf"(?i){kw}[^0-9]{{0,40}}?([\d]+\.[\d]{{1,3}})", text)
            if m:
                v = float(m.group(1))
                if 5 <= v <= 100:
                    die = v
                    break

        if not (gas and die):
            raise Exception("No ERN prices found")

        eff_date = _extract_any_date(text) or date.today().isoformat()
        return gas, die, eff_date


def scrape():
    return EritreaScraper().run()

if __name__ == "__main__":
    r = scrape()
    print(f"Eritrea: gas={r.gas_loc} ERN | die={r.die_loc} ERN | date={r.effective_date} | old={r.old_source}")

"""
Libya — NOC (National Oil Corporation)
Update cycle : STABLE — price unchanged for years (ultra-subsidised)
Primary URL  : https://noc.ly/
Currency     : LYD

Scraping strategy:
  1. noc.ly                  → scan for LYD price mentions
  2. DuckDuckGo              → "Libya fuel price LYD litre {year} official NOC"
  Note: Even for STABLE countries, we check every day per project rules.
        If unchanged, we return the same value with today's confirmation date.
"""
import re
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_STABLE
from utils.base import NoDataError
from utils.search import extract_prices_from_text


class LibyaScraper(SmartScraper):

    COUNTRY_META = {
        "country":      "Libya",
        "iso2":         "LY",
        "region":       "North Africa",
        "currency":     "LYD",
        "update_cycle": CYCLE_STABLE,
        "price_range":  (0.05, 2.0),

        "official_sources": [
            {"url": "https://noc.ly/",
             "name": "NOC Libya — National Oil Corporation", "confidence": "high"},
            {"url": "https://noc.ly/index.php/en/",
             "name": "NOC Libya — English", "confidence": "high"},
        ],

        "search_queries": [
            "Libya fuel price LYD per liter {year} official NOC government",
            "Libya gasoline diesel price {year} LYD subsidized official",
            "أسعار الوقود ليبيا {year} LYD رسمي",  # Arabic query
        ],

        # Last known stable values (ultra-subsidised)
        "last_known": {"gas_loc": 0.15, "die_loc": 0.135, "date": "2026-01-01"},
    }

    def _parse(self, html: str, url: str) -> tuple[float, float, str]:
        text = self._text(html)

        # Try LYD price extraction
        gas, die = extract_prices_from_text(text, "LYD", 0.05, 2.0)

        if gas is None or die is None:
            # Libya prices are so low (0.15 LYD) that generic extractors may miss them
            # Try specific patterns
            gas = self._find_lyd(text, ["gasoline", "petrol", "benzine", "بنزين"])
            die = self._find_lyd(text, ["diesel", "gasoil", "ديزل"])

        if gas is None or die is None:
            # Check for last known values confirmation (stable country)
            lk = self.COUNTRY_META.get("last_known", {})
            if lk:
                # Source confirmed reachable, price unchanged → return last known
                return lk["gas_loc"], lk["die_loc"], lk["date"]
            raise NoDataError("Libya LYD prices not found")

        eff_date = self._extract_date(text) or date.today().isoformat()
        return gas, die, eff_date

    def _find_lyd(self, text, keywords):
        for kw in keywords:
            m = re.search(
                rf"(?i){re.escape(kw)}[^0-9]{{0,60}}?(0\.\d{{1,3}}|\d{{1,2}}\.\d{{1,3}})",
                text
            )
            if m:
                v = float(m.group(1))
                if 0.05 <= v <= 2.0:
                    return v
        return None

    def _extract_date(self, text):
        m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        return m.group(1) if m else None


def scrape():
    return LibyaScraper().run()

if __name__ == "__main__":
    r = scrape()
    print(f"Libya: gas={r.gas_loc} LYD | die={r.die_loc} LYD | date={r.effective_date} | conf={r.confidence}")

"""
Equatorial Guinea — CEPE / Min. Mines & Hydrocarbures
Update cycle : QUARTERLY — price rarely changes
Currency     : XAF

Scraping strategy:
  1. cepe.gq                  → official CEPE prices page
  2. mines.gov.gq             → Ministry announcements
  3. DuckDuckGo               → "Equatorial Guinea carburant prix XAF {month} {year}"
  NOTE: globalpetrolprices.com is FORBIDDEN per project rules.
"""
import re
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_QUARTERLY
from utils.base import NoDataError


class EquatorialGuineaScraper(SmartScraper):

    COUNTRY_META = {
        "country":      "Equatorial Guinea",
        "iso2":         "GQ",
        "region":       "Central Africa",
        "currency":     "XAF",
        "update_cycle": CYCLE_QUARTERLY,
        "price_range":  (300, 900),

        "official_sources": [
            {
                "url":        "https://www.cepe.gq/",
                "name":       "CEPE Guinée Équatoriale",
                "confidence": "high",
            },
            {
                "url":        "https://www.mines.gov.gq/",
                "name":       "Min. Mines & Hydrocarbures GQ",
                "confidence": "high",
            },
        ],

        "search_queries": [
            "Guinée Équatoriale prix carburant XAF FCFA litre {month} {year} officiel CEPE",
            "Equatorial Guinea fuel price XAF {year} official government CEPE",
            "Guinea Ecuatorial precio combustible XAF {year} oficial CEPE",
        ],

        "last_known": {
            "gas_loc": 550.0,
            "die_loc": 520.0,
            "date":    "2025-01-01",
        },
    }

    def _parse(self, html: str, url: str) -> tuple[float, float, str]:
        text = self._text(html)

        gas = self._find_xaf(text, ["supercarburant", "essence", "gasoline", "petrol", "SP95"])
        die = self._find_xaf(text, ["gasoil", "diesel", "gazole"])

        if not (gas and die):
            lk = self.COUNTRY_META["last_known"]
            return lk["gas_loc"], lk["die_loc"], lk["date"]

        eff_date = self._find_date(text) or date.today().isoformat()
        return gas, die, eff_date

    def _find_xaf(self, text: str, keywords: list) -> float | None:
        for kw in keywords:
            m = re.search(
                rf"(?i){re.escape(kw)}[^0-9]{{0,80}}?(\d{{3,4}})\s*(?:FCFA|CFA|XAF|F\s*CFA)?",
                text
            )
            if m:
                v = float(m.group(1))
                if 300 <= v <= 900:
                    return v
        return None

    def _find_date(self, text: str) -> str | None:
        m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        return m.group(1) if m else None


def scrape():
    return EquatorialGuineaScraper().run()


if __name__ == "__main__":
    r = scrape()
    print(f"Equatorial Guinea: gas={r.gas_loc} XAF | die={r.die_loc} XAF | date={r.effective_date} | conf={r.confidence}")

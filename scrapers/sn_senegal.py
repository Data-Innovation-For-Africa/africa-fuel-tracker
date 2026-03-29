"""
Senegal — CRSE / Primature
Update cycle : Variable (decree published irregularly, last: 6-Dec-2025)
Primary URL  : https://primature.sn/publications/communiques-officiels/
Currency     : XOF

Scraping strategy:
  1. Primature communiqué direct URL (known decree URL)
  2. energie.gouv.sn          → scan for XOF price mentions
  3. DuckDuckGo               → "Sénégal prix carburant FCFA {month} {year} arrêté officiel"
"""
import re
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_VARIABLE
from utils.base import NoDataError

MONTHS_FR = {
    "janvier":"01","février":"02","mars":"03","avril":"04","mai":"05","juin":"06",
    "juillet":"07","août":"08","septembre":"09","octobre":"10","novembre":"11","décembre":"12"
}


class SenegalScraper(SmartScraper):

    COUNTRY_META = {
        "country":      "Senegal",
        "iso2":         "SN",
        "region":       "West Africa",
        "currency":     "XOF",
        "update_cycle": CYCLE_VARIABLE,
        "price_range":  (600, 1400),

        "official_sources": [
            # Known decree URL (Dec-2025 reduction)
            {"url": "https://primature.sn/publications/communiques-officiels/baisse-des-prix-des-hydrocarbures",
             "name": "Primature Sénégal — Communiqué prix hydrocarbures", "confidence": "high"},
            {"url": "https://www.energie.gouv.sn/",
             "name": "Min. Énergie Sénégal", "confidence": "high"},
            {"url": "https://primature.sn/publications/communiques-officiels/",
             "name": "Primature Sénégal — Communiqués", "confidence": "high"},
        ],

        "search_queries": [
            "Sénégal prix carburant supercarburant gasoil FCFA {month} {year} arrêté officiel",
            "site:primature.sn prix hydrocarbures {year}",
            "Sénégal CRSE baisse hausse prix carburant {year} FCFA litre",
        ],
    }

    def _parse(self, html: str, url: str) -> tuple[float, float, str]:
        text = self._text(html)
        gas, die = self._find_xof_prices(text)
        if not (gas and die):
            raise NoDataError("XOF fuel prices not found")
        eff_date = self._find_date(text) or date.today().isoformat()
        return gas, die, eff_date

    def _find_xof_prices(self, text):
        gas = die = None
        # Gas patterns: "supercarburant : 920 FCFA" "920 FCFA le litre"
        for pat in [
            r"supercarburant[^0-9]{0,40}?(\d{3,4})\s*(?:FCFA|CFA|F\s*CFA)",
            r"(?:essence|SP\s*95|benzine)[^0-9]{0,40}?(\d{3,4})\s*(?:FCFA|CFA)",
            r"(\d{3,4})\s*(?:FCFA|CFA)[^.]{0,40}?supercarburant",
            r"Nouveau prix\s*:\s*(\d{3,4})\s*FCFA.*?supercarburant",
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                v = float(m.group(1))
                if 600 <= v <= 1400:
                    gas = v
                    break

        # Diesel patterns
        for pat in [
            r"gasoil[^0-9]{0,40}?(\d{3,4})\s*(?:FCFA|CFA|F\s*CFA)",
            r"ga[sz]oil[^0-9]{0,40}?(\d{3,4})\s*(?:FCFA|CFA)",
            r"diesel[^0-9]{0,40}?(\d{3,4})\s*(?:FCFA|CFA)",
            r"(\d{3,4})\s*(?:FCFA|CFA)[^.]{0,40}?gasoil",
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                v = float(m.group(1))
                if 600 <= v <= 1400:
                    die = v
                    break

        return gas, die

    def _find_date(self, text):
        m = re.search(
            r"(\d{1,2})\s+(" + "|".join(MONTHS_FR.keys()) + r")\s+(\d{4})",
            text, re.IGNORECASE
        )
        if m:
            mn = MONTHS_FR.get(m.group(2).lower(), "01")
            return f"{m.group(3)}-{mn}-{m.group(1).zfill(2)}"
        m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        return m.group(1) if m else None


def scrape():
    return SenegalScraper().run()

if __name__ == "__main__":
    r = scrape()
    print(f"Senegal: gas={r.gas_loc} XOF | die={r.die_loc} XOF | date={r.effective_date} | conf={r.confidence}")

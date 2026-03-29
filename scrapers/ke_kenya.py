"""
Kenya — EPRA (Energy and Petroleum Regulatory Authority)
Update cycle : Monthly on the 15th  (CYCLE_MONTHLY_15)
Primary URL  : https://www.epra.go.ke/pump-prices
Currency     : KES

Scraping strategy:
  1. epra.go.ke/pump-prices  → parse ticker + price table
  2. epra.go.ke home         → scan for price mentions
  3. DuckDuckGo              → "Kenya EPRA fuel prices {month} {year} KES Nairobi"
"""
import re
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_15
from utils.base import NoDataError


class KenyaScraper(SmartScraper):

    COUNTRY_META = {
        "country":      "Kenya",
        "iso2":         "KE",
        "region":       "East Africa",
        "currency":     "KES",
        "update_cycle": CYCLE_MONTHLY_15,
        "price_range":  (100, 250),

        "official_sources": [
            {"url": "https://www.epra.go.ke/pump-prices",
             "name": "EPRA Kenya — Pump Prices", "confidence": "high"},
            {"url": "https://www.epra.go.ke/",
             "name": "EPRA Kenya — Homepage", "confidence": "high"},
        ],

        "search_queries": [
            "EPRA Kenya pump prices {month} {year} KES per liter Nairobi official",
            "site:epra.go.ke maximum retail petroleum prices {year}",
            "Kenya EPRA fuel price PMS AGO Nairobi {month} {year}",
        ],
    }

    def _parse(self, html: str, url: str) -> tuple[float, float, str]:
        text = self._text(html)
        soup = self._soup(html)

        gas = self._find_nairobi(text, ["PMS", "Super Petrol", "Petrol"])
        die = self._find_nairobi(text, ["AGO", "Diesel"])

        if not (gas and die):
            gas, die = self._from_table(soup)

        if not (gas and die):
            raise NoDataError("Nairobi PMS/AGO prices not found on page")

        eff_date = self._epra_date(text) or date.today().isoformat()
        return gas, die, eff_date

    def _find_nairobi(self, text, keywords):
        for kw in keywords:
            m = re.search(rf"Nairobi\s+{re.escape(kw)}\s+([\d,]+\.?\d*)", text, re.IGNORECASE)
            if m:
                v = float(m.group(1).replace(",", ""))
                if 100 <= v <= 250:
                    return v
        return None

    def _from_table(self, soup):
        gas = die = None
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                t = " ".join(cells).upper()
                nums = [float(n) for n in re.findall(r"\b(\d{3}\.?\d{0,2})\b", " ".join(cells))
                        if 100 <= float(n) <= 250]
                if "NAIROBI" in t and nums:
                    if ("PMS" in t or "PETROL" in t) and gas is None:
                        gas = nums[0]
                    if ("AGO" in t or "DIESEL" in t) and die is None:
                        die = nums[0]
        return gas, die

    def _epra_date(self, text):
        months = {"january":"01","february":"02","march":"03","april":"04",
                  "may":"05","june":"06","july":"07","august":"08",
                  "september":"09","october":"10","november":"11","december":"12"}
        m = re.search(
            r"(\d{1,2})(?:st|nd|rd|th)?\s+"
            r"(January|February|March|April|May|June|July|August|"
            r"September|October|November|December)\s+(\d{4})",
            text, re.IGNORECASE
        )
        if m:
            return f"{m.group(3)}-{months[m.group(2).lower()]}-{m.group(1).zfill(2)}"
        return None


def scrape():
    return KenyaScraper().run()

if __name__ == "__main__":
    r = scrape()
    print(f"Kenya: gas={r.gas_loc} KES | die={r.die_loc} KES | date={r.effective_date} | conf={r.confidence}")

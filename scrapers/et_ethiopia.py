"""
Ethiopia — Ministry of Trade and Regional Integration / EPSE
Update cycle : Monthly (variable day, typically 10th-15th)
Primary URL  : https://www.2merkato.com/news/energy-and-mining/
Currency     : ETB

Scraping strategy:
  1. addisinsight.net         → Ethiopian fuel price news (most reliable)
  2. 2merkato.com             → Ministry of Trade announcements
  3. epse.gov.et              → official EPSE site (often slow/down)
  4. DuckDuckGo               → "Ethiopia fuel price ETB birr {month} {year} EPSE Ministry"
"""
import re
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError


class EthiopiaScraper(SmartScraper):

    COUNTRY_META = {
        "country":      "Ethiopia",
        "iso2":         "ET",
        "region":       "East Africa",
        "currency":     "ETB",
        "update_cycle": CYCLE_MONTHLY_ANY,
        "price_range":  (60, 250),

        "official_sources": [
            {"url": "https://addisinsight.net/category/economy/",
             "name": "Addis Insight — Economy (fuel prices)", "confidence": "high"},
            {"url": "https://www.2merkato.com/news/energy-and-mining/",
             "name": "2merkato — Ministry of Trade announcements", "confidence": "high"},
            {"url": "https://www.epse.gov.et/",
             "name": "EPSE — Ethiopian Petroleum Supply Enterprise", "confidence": "high"},
            {"url": "https://birrmetrics.com/category/fuel/",
             "name": "Birr Metrics — Fuel prices", "confidence": "medium"},
        ],

        "search_queries": [
            "Ethiopia fuel price birr ETB {month} {year} EPSE Ministry Trade gasoline diesel official",
            "site:addisinsight.net fuel prices {year}",
            "Ethiopia benzene diesel price {year} ETB per liter Ministry announcement",
            "Ethiopia \"132\" OR \"139\" OR \"129\" birr fuel {year}",  # known recent values
        ],
    }

    def _parse(self, html: str, url: str) -> tuple[float, float, str]:
        text = self._text(html)
        gas, die = self._find_etb(text)
        if not (gas and die):
            raise NoDataError("ETB fuel prices not found in page")
        eff_date = self._find_date(text) or date.today().isoformat()
        return gas, die, eff_date

    def _find_etb(self, text):
        gas = die = None

        # Gasoline / benzene / petrol
        for pat in [
            r"[Gg]asoline[^0-9]{0,50}?(1\d{2}\.?\d{0,2})\s*(?:birr|ETB|Birr)",
            r"[Bb]enzene?[^0-9]{0,50}?(1\d{2}\.?\d{0,2})\s*(?:birr|ETB|Birr)",
            r"[Pp]etrol[^0-9]{0,50}?(1\d{2}\.?\d{0,2})\s*(?:birr|ETB|Birr)",
            r"(1\d{2}\.?\d{0,2})\s*(?:birr|ETB)[^.]{0,60}?(?:gasoline|benzene|petrol)",
            # Pattern from Ministry announcements: "Birr 132.18 per litre"
            r"[Bb]irr\s*(1[0-9]{2}\.?\d{0,2})[^.]{0,40}?(?:gasoline|benzene|petrol)",
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                v = float(m.group(1).rstrip("."))
                if 60 <= v <= 250:
                    gas = v
                    break

        # Diesel / white diesel
        for pat in [
            r"(?:white\s+)?[Dd]iesel[^0-9]{0,50}?(1\d{2}\.?\d{0,2})\s*(?:birr|ETB|Birr)",
            r"(1\d{2}\.?\d{0,2})\s*(?:birr|ETB)[^.]{0,60}?(?:diesel|gasoil)",
            r"[Bb]irr\s*(1[0-9]{2}\.?\d{0,2})[^.]{0,40}?diesel",
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                v = float(m.group(1).rstrip("."))
                if 60 <= v <= 250:
                    die = v
                    break

        return gas, die

    def _find_date(self, text):
        months = {"january":"01","february":"02","march":"03","april":"04",
                  "may":"05","june":"06","july":"07","august":"08",
                  "september":"09","october":"10","november":"11","december":"12"}
        # "effective March 10, 2026" or "10 March 2026"
        for pat in [
            r"[Mm]arch\s+(\d{1,2}),?\s+(\d{4})",
            r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
            r"\b(\d{4}-\d{2}-\d{2})\b",
        ]:
            m = re.search(pat, text)
            if m:
                if "-" in m.group(0):
                    return m.group(0)
                groups = m.groups()
                if len(groups) == 2:  # "March 10, 2026"
                    return f"2026-03-{groups[0].zfill(2)}"
                day, mon, yr = groups
                return f"{yr}-{months[mon.lower()]}-{day.zfill(2)}"
        return None


def scrape():
    return EthiopiaScraper().run()

if __name__ == "__main__":
    r = scrape()
    print(f"Ethiopia: gas={r.gas_loc} ETB | die={r.die_loc} ETB | date={r.effective_date} | conf={r.confidence}")

"""Namibia — MME (monthly 1st)  Currency: NAD"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_1
from utils.base import NoDataError

class NamibiaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Namibia","iso2":"NA","region":"Southern Africa","currency":"NAD",
        "update_cycle":CYCLE_MONTHLY_1,"price_range":(14,30),
        "official_sources":[
            {"url":"https://www.mme.gov.na/news/148/Fuel-Price-Review-Announcement-March-2026",
             "name":"MME Namibia — Fuel Price Review March 2026","confidence":"high"},
            {"url":"https://www.mme.gov.na/news/","name":"MME Namibia — News","confidence":"high"},
        ],
        "search_queries":[
            "Namibia MME fuel price NAD dollar per liter {month} {year} official Walvis Bay",
            "site:mme.gov.na fuel price review {year}",
            "Namibia petrol diesel price {month} {year} NAD MME official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._nad(t, ["petrol","Unleaded","95 ULP","gasoline"], 14, 30)
        die = self._nad(t, ["diesel","50ppm","500ppm"], 14, 30)
        if not (gas and die): raise NoDataError("NAD prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _nad(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2}}\.\d{{2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return NamibiaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Namibia: gas={r.gas_loc} NAD | die={r.die_loc} NAD | {r.effective_date}")

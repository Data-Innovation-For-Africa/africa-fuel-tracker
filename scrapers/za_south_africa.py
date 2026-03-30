"""South Africa — DMRE (monthly first Wednesday)  Currency: ZAR"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class SouthAfricaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"South Africa","iso2":"ZA","region":"Southern Africa","currency":"ZAR",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(14,30),
        "last_known":{"gas_loc":20.75,"die_loc":18.42,"date":"2026-03-04"},
        "official_sources":[
            {"url":"https://www.dmre.gov.za/energy-resources/energy-sources/pretoleum/fuel-prices",
             "name":"DMRE South Africa — Fuel Prices","confidence":"high"},
            {"url":"https://www.dmre.gov.za/news-room/","name":"DMRE Newsroom","confidence":"high"},
        ],
        "search_queries":[
            "South Africa DMRE fuel price ZAR rand per liter {month} {year} official coastal Gauteng",
            "site:dmre.gov.za fuel prices {year}",
            "South Africa petrol diesel price {month} {year} ZAR DMRE official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._zar(t, ["95 ULP","petrol","93 ULP","gasoline","unleaded"], 14, 30)
        die = self._zar(t, ["diesel 50ppm","diesel 500ppm","diesel","gasoil"], 14, 30)
        if not (gas and die): raise NoDataError("ZAR prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _zar(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2}}\.\d{{2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return SouthAfricaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"South Africa: gas={r.gas_loc} ZAR | die={r.die_loc} ZAR | {r.effective_date}")

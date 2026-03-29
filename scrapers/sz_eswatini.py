"""Eswatini — DMRE SA peg (1:1 ZAR)  Currency: SZL"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class EswatiniScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Eswatini","iso2":"SZ","region":"Southern Africa","currency":"SZL",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(14,30),
        "official_sources":[
            {"url":"https://www.dmre.gov.za/energy-resources/energy-sources/pretoleum/fuel-prices",
             "name":"DMRE South Africa (SZL pegged 1:1 ZAR)","confidence":"high"},
        ],
        "search_queries":[
            "Eswatini Swaziland fuel price SZL lilangeni per liter {month} {year} official",
            "Eswatini petrol diesel price {month} {year} SZL official ZAR peg",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._szl(t, ["petrol","95 ULP","gasoline","unleaded"], 14, 30)
        die = self._szl(t, ["diesel","50ppm","500ppm","gasoil"], 14, 30)
        if not (gas and die): raise NoDataError("SZL prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _szl(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2}}\.\d{{2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return EswatiniScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Eswatini: gas={r.gas_loc} SZL | die={r.die_loc} SZL | {r.effective_date}")

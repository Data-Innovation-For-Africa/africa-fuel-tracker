"""South Sudan — Eye Radio / BoSS  Currency: SSP"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_VARIABLE
from utils.base import NoDataError

class SouthSudanScraper(SmartScraper):
    COUNTRY_META = {
        "country":"South Sudan","iso2":"SS","region":"East Africa","currency":"SSP",
        "update_cycle":CYCLE_VARIABLE,"price_range":(3000,60000),
        "official_sources":[
            {"url":"https://www.eyeradio.org/","name":"Eye Radio South Sudan","confidence":"medium"},
            {"url":"https://mop.gov.ss/","name":"Ministry of Petroleum South Sudan","confidence":"high"},
        ],
        "search_queries":[
            "South Sudan fuel price SSP pounds per liter Juba {month} {year} official",
            "site:eyeradio.org fuel price Juba {year}",
            "South Sudan petrol diesel price {year} SSP Juba pump",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._ssp(t, ["gasoline","petrol","benzine"], 3000, 60000)
        die = self._ssp(t, ["diesel","gasoil"], 3000, 60000)
        if not (gas and die): raise NoDataError("SSP prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _ssp(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{4,6}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return SouthSudanScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"South Sudan: gas={r.gas_loc} SSP | die={r.die_loc} SSP | {r.effective_date}")

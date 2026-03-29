"""Sierra Leone — NPRA (National Petroleum Regulatory Agency)  Currency: SLL"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class SierraLeoneScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Sierra Leone","iso2":"SL","region":"West Africa","currency":"SLL",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(15000,60000),
        "official_sources":[
            {"url":"https://www.npra.gov.sl/","name":"NPRA Sierra Leone","confidence":"high"},
            {"url":"https://www.npra.gov.sl/price-announcement/","name":"NPRA — Price Announcement","confidence":"high"},
        ],
        "search_queries":[
            "Sierra Leone NPRA fuel price SLL leones per liter {month} {year} official",
            "Sierra Leone petrol diesel price {month} {year} SLL NPRA official announcement",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._sll(t, ["petrol","gasoline","Premium"], 15000, 60000)
        die = self._sll(t, ["diesel","gasoil","AGO"], 15000, 60000)
        if not (gas and die): raise NoDataError("SLL prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _sll(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{4,6}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return SierraLeoneScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Sierra Leone: gas={r.gas_loc} SLL | die={r.die_loc} SLL | {r.effective_date}")

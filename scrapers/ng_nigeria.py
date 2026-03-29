"""Nigeria — NNPC Limited (deregulated market)  Currency: NGN"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_WEEKLY
from utils.base import NoDataError

class NigeriaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Nigeria","iso2":"NG","region":"West Africa","currency":"NGN",
        "update_cycle":CYCLE_WEEKLY,"price_range":(600,3000),
        "official_sources":[
            {"url":"https://www.nnpcgroup.com/","name":"NNPC Limited Nigeria","confidence":"high"},
            {"url":"https://www.nnpcgroup.com/NNPC-Business/Downstream-Ventures/Pages/Retail.aspx","name":"NNPC Retail","confidence":"high"},
            {"url":"https://nnpcretail.com/","name":"NNPC Retail Prices","confidence":"high"},
        ],
        "search_queries":[
            "Nigeria NNPC fuel price NGN naira per liter {month} {year} Lagos official",
            "Nigeria petrol diesel price {month} {year} NGN official NNPC",
            "Nigeria fuel price increase {year} naira liter NNPC",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._ngn(t, ["petrol","PMS","Premium Motor Spirit","gasoline"], 600, 3000)
        die = self._ngn(t, ["diesel","AGO","Automotive Gas"], 600, 3000)
        if not (gas and die): raise NoDataError("NGN prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _ngn(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{3,4}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return NigeriaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Nigeria: gas={r.gas_loc} NGN | die={r.die_loc} NGN | {r.effective_date}")

"""Ghana — NPA (National Petroleum Authority) bimonthly  Currency: GHS"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_BIMONTHLY
from utils.base import NoDataError

class GhanaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Ghana","iso2":"GH","region":"West Africa","currency":"GHS",
        "update_cycle":CYCLE_BIMONTHLY,"price_range":(8,30),
        "official_sources":[
            {"url":"https://www.npa.gov.gh/","name":"NPA Ghana","confidence":"high"},
            {"url":"https://www.npa.gov.gh/price-floor","name":"NPA Ghana — Price Floor","confidence":"high"},
            {"url":"https://www.npa.gov.gh/2025/price-build-up","name":"NPA Ghana — Price Build-up","confidence":"high"},
        ],
        "search_queries":[
            "Ghana NPA fuel price GHS cedi per liter {month} {year} official",
            "site:npa.gov.gh price floor {year}",
            "Ghana petrol diesel price {month} {year} GHS NPA official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._ghs(t, ["gasoline","petrol","Premium Motor Spirit","PMS"], 8, 30)
        die = self._ghs(t, ["diesel","AGO","Automotive Gas Oil"], 8, 30)
        if not (gas and die): raise NoDataError("GHS prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _ghs(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,60}}?(\d{{1,2}}\.\d{{2,3}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return GhanaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Ghana: gas={r.gas_loc} GHS | die={r.die_loc} GHS | {r.effective_date}")

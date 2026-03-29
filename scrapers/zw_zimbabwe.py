"""Zimbabwe — ZERA (weekly)  Currency: ZWG"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_WEEKLY
from utils.base import NoDataError

class ZimbabweScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Zimbabwe","iso2":"ZW","region":"Southern Africa","currency":"ZWG",
        "update_cycle":CYCLE_WEEKLY,"price_range":(800,5000),
        "official_sources":[
            {"url":"https://www.zera.co.zw/","name":"ZERA Zimbabwe","confidence":"high"},
            {"url":"https://www.zera.co.zw/fuel-prices/","name":"ZERA — Fuel Prices","confidence":"high"},
        ],
        "search_queries":[
            "Zimbabwe ZERA fuel price ZWG per liter {month} {year} official Harare",
            "site:zera.co.zw fuel prices {year}",
            "Zimbabwe petrol diesel price {month} {year} ZWG ZERA official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._zwg(t, ["petrol","gasoline","Premium"], 800, 5000)
        die = self._zwg(t, ["diesel","AGO"], 800, 5000)
        if not (gas and die): raise NoDataError("ZWG prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _zwg(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{3,4}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return ZimbabweScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Zimbabwe: gas={r.gas_loc} ZWG | die={r.die_loc} ZWG | {r.effective_date}")

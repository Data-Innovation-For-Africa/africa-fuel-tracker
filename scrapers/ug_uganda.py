"""Uganda — PAU (Petroleum Authority of Uganda)  Currency: UGX"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_WEEKLY
from utils.base import NoDataError

class UgandaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Uganda","iso2":"UG","region":"East Africa","currency":"UGX",
        "update_cycle":CYCLE_WEEKLY,"price_range":(3000,8000),
        "official_sources":[
            {"url":"https://www.pau.go.ug/","name":"PAU Uganda","confidence":"high"},
            {"url":"https://www.pau.go.ug/petroleum-prices/","name":"PAU — Petroleum Prices","confidence":"high"},
        ],
        "search_queries":[
            "Uganda PAU fuel price UGX shilling per liter {month} {year} Kampala official",
            "Uganda petrol diesel price {month} {year} UGX PAU",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._ugx(t, ["petrol","gasoline","Premium"], 3000, 8000)
        die = self._ugx(t, ["diesel","AGO"], 3000, 8000)
        if not (gas and die): raise NoDataError("UGX prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _ugx(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{4,5}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return UgandaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Uganda: gas={r.gas_loc} UGX | die={r.die_loc} UGX | {r.effective_date}")

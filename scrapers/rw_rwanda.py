"""Rwanda — RURA (bimonthly)  Currency: RWF"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_BIMONTHLY
from utils.base import NoDataError

class RwandaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Rwanda","iso2":"RW","region":"East Africa","currency":"RWF",
        "update_cycle":CYCLE_BIMONTHLY,"price_range":(1000,3000),
        "official_sources":[
            {"url":"https://www.rura.rw/index.php/en/fuel-prices","name":"RURA Rwanda — Fuel Prices","confidence":"high"},
            {"url":"https://www.rura.rw/","name":"RURA Rwanda","confidence":"high"},
        ],
        "search_queries":[
            "Rwanda RURA fuel price RWF franc per liter {month} {year} official Kigali",
            "site:rura.rw fuel prices {year}",
            "Rwanda petrol diesel price {month} {year} RWF RURA official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._rwf(t, ["petrol","gasoline","Premium"], 1000, 3000)
        die = self._rwf(t, ["diesel","AGO"], 1000, 3000)
        if not (gas and die): raise NoDataError("RWF prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _rwf(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{4}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return RwandaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Rwanda: gas={r.gas_loc} RWF | die={r.die_loc} RWF | {r.effective_date}")

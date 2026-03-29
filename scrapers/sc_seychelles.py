"""Seychelles — PUC (monthly)  Currency: SCR"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class SeychellesScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Seychelles","iso2":"SC","region":"East Africa","currency":"SCR",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(12,35),
        "official_sources":[
            {"url":"https://www.puc.sc/","name":"PUC Seychelles","confidence":"high"},
            {"url":"https://www.puc.sc/fuel-prices/","name":"PUC — Fuel Prices","confidence":"high"},
        ],
        "search_queries":[
            "Seychelles PUC fuel price SCR rupee per liter {month} {year} official",
            "Seychelles petrol diesel price {month} {year} SCR PUC official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._scr(t, ["petrol","gasoline","motor spirit"], 12, 35)
        die = self._scr(t, ["diesel","gasoil"], 12, 35)
        if not (gas and die): raise NoDataError("SCR prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _scr(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return SeychellesScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Seychelles: gas={r.gas_loc} SCR | die={r.die_loc} SCR | {r.effective_date}")

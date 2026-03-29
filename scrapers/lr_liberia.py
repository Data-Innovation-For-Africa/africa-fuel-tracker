"""Liberia — NOCAL (National Oil Company)  Currency: LRD"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_QUARTERLY
from utils.base import NoDataError

class LiberiaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Liberia","iso2":"LR","region":"West Africa","currency":"LRD",
        "update_cycle":CYCLE_QUARTERLY,"price_range":(100,350),
        "official_sources":[
            {"url":"https://www.nocal.com.lr/","name":"NOCAL Liberia","confidence":"high"},
            {"url":"https://www.nocal.com.lr/fuel-prices/","name":"NOCAL — Fuel Prices","confidence":"high"},
        ],
        "search_queries":[
            "Liberia fuel price LRD dollar per liter {year} NOCAL official",
            "Liberia petrol diesel price {year} Monrovia official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._lrd(t, ["petrol","gasoline","Premium"], 100, 350)
        die = self._lrd(t, ["diesel","gasoil"], 100, 350)
        if not (gas and die): raise NoDataError("LRD prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _lrd(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2,3}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return LiberiaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Liberia: gas={r.gas_loc} LRD | die={r.die_loc} LRD | {r.effective_date}")

"""Algeria — ARH/Naftal via thefuelprice.com (naftal.dz offline)
Cycle: STABLE (annual, last change Jan-2026)  Currency: DZD"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_STABLE
from utils.base import NoDataError

class AlgeriaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Algeria","iso2":"DZ","region":"North Africa","currency":"DZD",
        "update_cycle":CYCLE_STABLE,"price_range":(20,120),
        "official_sources":[
            {"url":"https://www.thefuelprice.com/Fdz/en","name":"TheFuelPrice Algeria","confidence":"high"},
            {"url":"https://www.naftal.dz/","name":"Naftal DZ","confidence":"high"},
        ],
        "search_queries":[
            "Algeria fuel price DZD dinar per liter {year} official ARH Naftal",
            "prix carburant Algérie DZD litre {year} officiel ARH",
        ],
        "last_known":{"gas_loc":47.0,"die_loc":31.0,"date":"2026-01-01"},
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._find(t, ["gasoline","petrol","essence","super","SP95"], 20, 120)
        die = self._find(t, ["diesel","gasoil"], 20, 120)
        if not (gas and die):
            lk = self.COUNTRY_META["last_known"]
            return lk["gas_loc"], lk["die_loc"], lk["date"]
        return gas, die, self._date(t) or date.today().isoformat()
    def _find(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,60}}?(\d{{2,3}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return AlgeriaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Algeria: gas={r.gas_loc} DZD | die={r.die_loc} DZD | {r.effective_date}")

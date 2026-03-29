"""Tunisia — STIR (stable regulated)  Currency: TND"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_STABLE
from utils.base import NoDataError

class TunisiaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Tunisia","iso2":"TN","region":"North Africa","currency":"TND",
        "update_cycle":CYCLE_STABLE,"price_range":(1.5,5.0),
        "official_sources":[
            {"url":"https://www.stir.com.tn/","name":"STIR Tunisie","confidence":"high"},
            {"url":"https://www.stir.com.tn/carburants","name":"STIR Tunisie — Carburants","confidence":"high"},
        ],
        "search_queries":[
            "Tunisia fuel price TND dinar per liter {year} official STIR",
            "prix carburant Tunisie TND litre {year} officiel STIR",
        ],
        "last_known":{"gas_loc":2.53,"die_loc":2.21,"date":"2026-01-01"},
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._find(t, ["SP95","super","essence","benzine","gasoline"], 1.5, 5.0)
        die = self._find(t, ["gasoil","diesel","gazole"], 1.5, 5.0)
        if not (gas and die):
            lk = self.COUNTRY_META["last_known"]
            return lk["gas_loc"], lk["die_loc"], lk["date"]
        return gas, die, self._date(t) or date.today().isoformat()
    def _find(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,60}}?(\d\.\d{{2,3}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return TunisiaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Tunisia: gas={r.gas_loc} TND | die={r.die_loc} TND | {r.effective_date}")

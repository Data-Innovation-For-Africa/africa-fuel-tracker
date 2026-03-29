"""Djibouti — ANE (Agence Nationale Énergie)  Currency: DJF"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_QUARTERLY
from utils.base import NoDataError

class DjiboutiScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Djibouti","iso2":"DJ","region":"East Africa","currency":"DJF",
        "update_cycle":CYCLE_QUARTERLY,"price_range":(120,400),
        "official_sources":[
            {"url":"https://www.ane.gouv.dj/","name":"ANE Djibouti","confidence":"high"},
            {"url":"https://www.ane.gouv.dj/prix-carburants/","name":"ANE — Prix Carburants","confidence":"high"},
        ],
        "search_queries":[
            "Djibouti fuel price DJF franc per liter {year} official ANE",
            "Djibouti prix carburant DJF franc {year} officiel ANE",
        ],
        "last_known":{"gas_loc":240.0,"die_loc":225.0,"date":"2026-01-01"},
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._djf(t, ["essence","super","gasoline","petrol"], 120, 400)
        die = self._djf(t, ["gasoil","diesel"], 120, 400)
        if not (gas and die):
            lk = self.COUNTRY_META["last_known"]
            return lk["gas_loc"], lk["die_loc"], lk["date"]
        return gas, die, self._date(t) or date.today().isoformat()
    def _djf(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2,3}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return DjiboutiScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Djibouti: gas={r.gas_loc} DJF | die={r.die_loc} DJF | {r.effective_date}")

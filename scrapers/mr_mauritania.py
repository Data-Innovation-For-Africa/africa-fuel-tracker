"""Mauritania — Min. Pétrole / APE  Currency: MRU"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_QUARTERLY
from utils.base import NoDataError

class MauritaniaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Mauritania","iso2":"MR","region":"West Africa","currency":"MRU",
        "update_cycle":CYCLE_QUARTERLY,"price_range":(25,80),
        "official_sources":[
            {"url":"https://www.petrole.gov.mr/","name":"Min. Pétrole Mauritanie","confidence":"high"},
            {"url":"https://www.petrole.gov.mr/prix-hydrocarbures/","name":"Min. Pétrole — Prix","confidence":"high"},
        ],
        "search_queries":[
            "Mauritanie prix carburant MRU ouguiya litre {year} officiel gouvernement",
            "Mauritania fuel price MRU {year} official petroleum ministry",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._mru(t, ["essence","super","gasoline","petrol"], 25, 80)
        die = self._mru(t, ["gasoil","diesel"], 25, 80)
        if not (gas and die): raise NoDataError("MRU prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _mru(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,60}}?(\d{{2,3}}\.?\d{{0,1}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return MauritaniaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Mauritania: gas={r.gas_loc} MRU | die={r.die_loc} MRU | {r.effective_date}")

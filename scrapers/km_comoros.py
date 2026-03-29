"""Comoros — Min. Énergie / oilpricez.com  Currency: KMF"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_QUARTERLY
from utils.base import NoDataError

class ComorosScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Comoros","iso2":"KM","region":"East Africa","currency":"KMF",
        "update_cycle":CYCLE_QUARTERLY,"price_range":(400,1200),
        "official_sources":[
            {"url":"https://oilpricez.com/km/comoros-oil-price","name":"oilpricez.com Comoros","confidence":"medium"},
            {"url":"https://www.gouvernement.km/","name":"Gouvernement Comores","confidence":"high"},
        ],
        "search_queries":[
            "Comoros fuel price KMF franc per liter {year} official government",
            "Comores prix carburant KMF {year} officiel gouvernement",
        ],
        "last_known":{"gas_loc":760.0,"die_loc":680.0,"date":"2026-03-16"},
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._kmf(t, ["gasoline","petrol","essence","1 Liter Price"], 400, 1200)
        die = self._kmf(t, ["diesel","gasoil"], 400, 1200)
        if not (gas and die):
            lk = self.COUNTRY_META["last_known"]
            return lk["gas_loc"], lk["die_loc"], lk["date"]
        return gas, die, self._date(t) or date.today().isoformat()
    def _kmf(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{3,4}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return ComorosScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Comoros: gas={r.gas_loc} KMF | die={r.die_loc} KMF | {r.effective_date}")

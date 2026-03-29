"""Madagascar — OMH (monthly)  Currency: MGA"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class MadagascarScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Madagascar","iso2":"MG","region":"East Africa","currency":"MGA",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(3500,9000),
        "official_sources":[
            {"url":"https://www.omh.mg/","name":"OMH Madagascar","confidence":"high"},
            {"url":"https://www.omh.mg/prix-carburants/","name":"OMH — Prix Carburants","confidence":"high"},
        ],
        "search_queries":[
            "Madagascar OMH prix carburant MGA ariary litre {month} {year} officiel",
            "Madagascar fuel price MGA {month} {year} official OMH",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._mga(t, ["essence","super","gasoline","petrol"], 3500, 9000)
        die = self._mga(t, ["gasoil","diesel","gazole"], 3500, 9000)
        if not (gas and die): raise NoDataError("MGA prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _mga(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{4,5}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return MadagascarScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Madagascar: gas={r.gas_loc} MGA | die={r.die_loc} MGA | {r.effective_date}")

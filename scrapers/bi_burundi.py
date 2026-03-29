"""Burundi — AREEN (bimonthly)  Currency: BIF"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_BIMONTHLY
from utils.base import NoDataError

class BurundiScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Burundi","iso2":"BI","region":"East Africa","currency":"BIF",
        "update_cycle":CYCLE_BIMONTHLY,"price_range":(2000,7000),
        "official_sources":[
            {"url":"https://www.areen.bi/","name":"AREEN Burundi","confidence":"high"},
            {"url":"https://www.areen.bi/prix-carburants/","name":"AREEN — Prix Carburants","confidence":"high"},
        ],
        "search_queries":[
            "Burundi AREEN prix carburant BIF franc litre {month} {year} officiel",
            "Burundi fuel price BIF {month} {year} official AREEN",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._bif(t, ["essence","super","gasoline","petrol"], 2000, 7000)
        die = self._bif(t, ["gasoil","diesel"], 2000, 7000)
        if not (gas and die): raise NoDataError("BIF prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _bif(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{4,5}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return BurundiScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Burundi: gas={r.gas_loc} BIF | die={r.die_loc} BIF | {r.effective_date}")

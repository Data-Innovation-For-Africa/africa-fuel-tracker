"""Mozambique — INP (monthly)  Currency: MZN"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class MozambiqueScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Mozambique","iso2":"MZ","region":"Southern Africa","currency":"MZN",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(50,140),
        "official_sources":[
            {"url":"https://www.inp.gov.mz/","name":"INP Mozambique","confidence":"high"},
            {"url":"https://www.inp.gov.mz/precos-combustiveis/","name":"INP — Preços Combustíveis","confidence":"high"},
        ],
        "search_queries":[
            "Mozambique INP fuel price MZN metical per liter {month} {year} official",
            "Moçambique preço combustível MZN {month} {year} oficial INP",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._mzn(t, ["gasolina","gasoline","petrol","super"], 50, 140)
        die = self._mzn(t, ["gasóleo","diesel","gasoil"], 50, 140)
        if not (gas and die): raise NoDataError("MZN prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _mzn(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2,3}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return MozambiqueScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Mozambique: gas={r.gas_loc} MZN | die={r.die_loc} MZN | {r.effective_date}")

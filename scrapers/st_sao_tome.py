"""Sao Tome — Governo STP  Currency: STN"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_QUARTERLY
from utils.base import NoDataError

class SaoTomeScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Sao Tome","iso2":"ST","region":"Central Africa","currency":"STN",
        "update_cycle":CYCLE_QUARTERLY,"price_range":(15,50),
        "official_sources":[
            {"url":"https://www.governo.st/","name":"Governo STP","confidence":"high"},
            {"url":"https://www.governo.st/economia/","name":"Governo STP — Economia","confidence":"high"},
        ],
        "search_queries":[
            "Sao Tome fuel price STN dobra per liter {year} official government",
            "São Tomé preço combustível STN {year} dobra gasolina gasóleo oficial",
        ],
        "last_known":{"gas_loc":28.0,"die_loc":25.5,"date":"2026-01-01"},
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._stn(t, ["gasolina","gasoline","petrol","super"], 15, 50)
        die = self._stn(t, ["gasóleo","diesel","gasoil"], 15, 50)
        if not (gas and die):
            lk = self.COUNTRY_META["last_known"]
            return lk["gas_loc"], lk["die_loc"], lk["date"]
        return gas, die, self._date(t) or date.today().isoformat()
    def _stn(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,60}}?(\d{{2}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return SaoTomeScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Sao Tome: gas={r.gas_loc} STN | die={r.die_loc} STN | {r.effective_date}")

"""Angola — IANPETRO/Sonangol (stable subsidised)  Currency: AOA"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_STABLE
from utils.base import NoDataError

class AngolaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Angola","iso2":"AO","region":"Southern Africa","currency":"AOA",
        "update_cycle":CYCLE_STABLE,"price_range":(150,700),
        "official_sources":[
            {"url":"https://www.ianpetro.ao/","name":"IANPETRO Angola","confidence":"high"},
            {"url":"https://www.ianpetro.ao/precos/","name":"IANPETRO — Preços","confidence":"high"},
        ],
        "search_queries":[
            "Angola fuel price AOA kwanza per liter {year} official IANPETRO Sonangol",
            "Angola gasolina diesel preço AOA {year} oficial IANPETRO",
        ],
        "last_known":{"gas_loc":300.0,"die_loc":400.0,"date":"2025-12-01"},
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._aoa(t, ["gasolina","gasoline","petrol","super"], 150, 700)
        die = self._aoa(t, ["gasóleo","diesel","gasoil"], 150, 700)
        if not (gas and die):
            lk = self.COUNTRY_META["last_known"]
            return lk["gas_loc"], lk["die_loc"], lk["date"]
        return gas, die, self._date(t) or date.today().isoformat()
    def _aoa(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2,3}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return AngolaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Angola: gas={r.gas_loc} AOA | die={r.die_loc} AOA | {r.effective_date}")

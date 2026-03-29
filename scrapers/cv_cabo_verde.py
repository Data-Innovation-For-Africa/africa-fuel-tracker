"""Cabo Verde — ARE (Agência Reguladora da Energia)  Currency: CVE"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class CaboVerdeScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Cabo Verde","iso2":"CV","region":"West Africa","currency":"CVE",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(70,200),
        "official_sources":[
            {"url":"https://www.are.cv/","name":"ARE Cabo Verde","confidence":"high"},
            {"url":"https://www.are.cv/preco-combustiveis/","name":"ARE — Preços Combustíveis","confidence":"high"},
        ],
        "search_queries":[
            "Cabo Verde fuel price CVE escudo per liter {month} {year} ARE official",
            "preço combustível Cabo Verde CVE {month} {year} ARE",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._cve(t, ["gasolina","gasoline","petrol"], 70, 200)
        die = self._cve(t, ["gasóleo","diesel","gasoil"], 70, 200)
        if not (gas and die): raise NoDataError("CVE prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _cve(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,60}}?(\d{{2,3}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return CaboVerdeScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Cabo Verde: gas={r.gas_loc} CVE | die={r.die_loc} CVE | {r.effective_date}")

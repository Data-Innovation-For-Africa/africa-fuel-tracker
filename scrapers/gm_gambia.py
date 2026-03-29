"""Gambia — Min. Finance/PSG  Currency: GMD"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_QUARTERLY
from utils.base import NoDataError

class GambiaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Gambia","iso2":"GM","region":"West Africa","currency":"GMD",
        "update_cycle":CYCLE_QUARTERLY,"price_range":(30,150),
        "official_sources":[
            {"url":"https://www.gambia.gov.gm/","name":"Gambia Government","confidence":"high"},
            {"url":"https://www.gambia.gov.gm/news","name":"Gambia Gov News","confidence":"high"},
        ],
        "search_queries":[
            "Gambia fuel price GMD dalasi per liter {year} official government",
            "Gambia petrol diesel price {year} GMD",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._find(t, ["petrol","gasoline","essence"], 30, 150)
        die = self._find(t, ["diesel","gasoil"], 30, 150)
        if not (gas and die): raise NoDataError("GMD prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _find(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,60}}?(\d{{2,3}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return GambiaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Gambia: gas={r.gas_loc} GMD | die={r.die_loc} GMD | {r.effective_date}")

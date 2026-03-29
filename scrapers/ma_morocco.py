"""Morocco — auto24.ma (deregulated market, weekly)  Currency: MAD"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_WEEKLY
from utils.base import NoDataError

class MoroccoScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Morocco","iso2":"MA","region":"North Africa","currency":"MAD",
        "update_cycle":CYCLE_WEEKLY,"price_range":(8,22),
        "official_sources":[
            {"url":"https://auto24.ma/en/fuel-price-tracker","name":"auto24.ma Morocco Fuel Tracker","confidence":"high"},
            {"url":"https://auto24.ma/fr/suivi-prix-carburant","name":"auto24.ma Maroc prix carburant","confidence":"high"},
        ],
        "search_queries":[
            "Morocco fuel price MAD dirham per liter {month} {year} official",
            "prix carburant Maroc MAD dirham litre {month} {year}",
            "Morocco gasoline diesel price {year} MAD",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._find(t, ["gasoline","petrol","essence","SP95","sans plomb"], 8, 22)
        die = self._find(t, ["diesel","gasoil","gazole"], 8, 22)
        if not (gas and die): raise NoDataError("MAD prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _find(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,60}}?(\d{{1,2}}\.\d{{1,3}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return MoroccoScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Morocco: gas={r.gas_loc} MAD | die={r.die_loc} MAD | {r.effective_date}")

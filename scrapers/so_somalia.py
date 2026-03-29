"""Somalia — NBS / dollarised market  Currency: USD"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_VARIABLE
from utils.base import NoDataError

class SomaliaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Somalia","iso2":"SO","region":"East Africa","currency":"USD",
        "update_cycle":CYCLE_VARIABLE,"price_range":(0.4,3.5),
        "official_sources":[
            {"url":"https://nbs.gov.so/","name":"NBS Somalia — National Bureau of Statistics","confidence":"high"},
            {"url":"https://www.eyeradio.org/","name":"Eye Radio Somalia — Fuel Prices","confidence":"medium"},
        ],
        "search_queries":[
            "Somalia fuel price USD per liter Mogadishu {month} {year} official",
            "Somalia gasoline diesel price {month} {year} Mogadishu USD",
            "site:eyeradio.org fuel price {year}",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._usd(t, ["gasoline","petrol","benzine"], 0.4, 3.5)
        die = self._usd(t, ["diesel","gasoil"], 0.4, 3.5)
        if not (gas and die): raise NoDataError("USD Somalia prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _usd(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?\$(\d+\.\d{{2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d+\.\d{{2}})[^0-9]{{0,20}}?(?:USD|dollar|per liter)", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return SomaliaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Somalia: gas={r.gas_loc} USD | die={r.die_loc} USD | {r.effective_date}")

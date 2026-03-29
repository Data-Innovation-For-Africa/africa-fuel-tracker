"""Tanzania — EWURA (monthly first Wednesday)  Currency: TZS"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class TanzaniaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Tanzania","iso2":"TZ","region":"East Africa","currency":"TZS",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(1500,5000),
        "official_sources":[
            {"url":"https://www.ewura.go.tz/faqs/petroleum-fuel-prices","name":"EWURA Tanzania — Petroleum Prices","confidence":"high"},
            {"url":"https://www.ewura.go.tz/","name":"EWURA Tanzania","confidence":"high"},
            {"url":"https://www.ewura.go.tz/publications/petroleum-price","name":"EWURA — Cap Prices","confidence":"high"},
        ],
        "search_queries":[
            "Tanzania EWURA cap prices TZS shilling per liter {month} {year} Dar es Salaam official",
            "site:ewura.go.tz cap prices petroleum {year}",
            "Tanzania fuel price TZS {month} {year} EWURA official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._tzs(t, ["petrol","PMS","gasoline"], 1500, 5000)
        die = self._tzs(t, ["diesel","AGO","gasoil"], 1500, 5000)
        if not (gas and die): raise NoDataError("TZS prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _tzs(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{4}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return TanzaniaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Tanzania: gas={r.gas_loc} TZS | die={r.die_loc} TZS | {r.effective_date}")

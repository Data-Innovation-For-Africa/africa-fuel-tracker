"""Botswana — BERA (monthly)  Currency: BWP"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class BotswanaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Botswana","iso2":"BW","region":"Southern Africa","currency":"BWP",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(10,28),
        "official_sources":[
            {"url":"https://www.bera.co.bw/","name":"BERA Botswana","confidence":"high"},
            {"url":"https://www.bera.co.bw/fuel-prices/","name":"BERA — Fuel Prices","confidence":"high"},
        ],
        "search_queries":[
            "Botswana BERA fuel price BWP pula per liter {month} {year} official",
            "Botswana petrol diesel price {month} {year} BWP BERA official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._bwp(t, ["petrol","gasoline","Unleaded"], 10, 28)
        die = self._bwp(t, ["diesel","gasoil"], 10, 28)
        if not (gas and die): raise NoDataError("BWP prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _bwp(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return BotswanaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Botswana: gas={r.gas_loc} BWP | die={r.die_loc} BWP | {r.effective_date}")

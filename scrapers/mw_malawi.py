"""Malawi — MERA (monthly)  Currency: MWK"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class MalawiScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Malawi","iso2":"MW","region":"East Africa","currency":"MWK",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(2000,10000),
        "official_sources":[
            {"url":"https://www.meramalawi.mw/","name":"MERA Malawi","confidence":"high"},
            {"url":"https://www.meramalawi.mw/fuel-prices/","name":"MERA — Fuel Prices","confidence":"high"},
        ],
        "search_queries":[
            "Malawi MERA fuel price MWK kwacha per liter {month} {year} official",
            "Malawi petrol diesel price {month} {year} MWK MERA official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._mwk(t, ["petrol","gasoline","Premium"], 2000, 10000)
        die = self._mwk(t, ["diesel","AGO"], 2000, 10000)
        if not (gas and die): raise NoDataError("MWK prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _mwk(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{4,5}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return MalawiScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Malawi: gas={r.gas_loc} MWK | die={r.die_loc} MWK | {r.effective_date}")

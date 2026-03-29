"""Lesotho — Min. Énergie / DMRE SA peg  Currency: LSL"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class LesothoScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Lesotho","iso2":"LS","region":"Southern Africa","currency":"LSL",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(14,28),
        "official_sources":[
            {"url":"https://www.energy.gov.ls/","name":"Min. Énergie Lesotho","confidence":"high"},
            {"url":"https://www.dmre.gov.za/energy-resources/energy-sources/pretoleum/fuel-prices",
             "name":"DMRE South Africa (LSL pegged to ZAR)","confidence":"high"},
        ],
        "search_queries":[
            "Lesotho fuel price LSL loti per liter {month} {year} official",
            "Lesotho petrol diesel price {month} {year} LSL official energy ministry",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._lsl(t, ["petrol","gasoline","unleaded","95"], 14, 28)
        die = self._lsl(t, ["diesel","gasoil","50ppm"], 14, 28)
        if not (gas and die): raise NoDataError("LSL prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _lsl(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2}}\.\d{{2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return LesothoScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Lesotho: gas={r.gas_loc} LSL | die={r.die_loc} LSL | {r.effective_date}")

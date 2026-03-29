"""Mauritius — STC/PPC (monthly)  Currency: MUR"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class MauritiusScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Mauritius","iso2":"MU","region":"East Africa","currency":"MUR",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(40,100),
        "official_sources":[
            {"url":"https://www.stcmu.com/ppm/press-release","name":"STC Mauritius — PPC Press Release","confidence":"high"},
            {"url":"https://www.stcmu.com/","name":"STC Mauritius","confidence":"high"},
        ],
        "search_queries":[
            "Mauritius STC PPC fuel price MUR rupee per liter {month} {year} official Mogas",
            "site:stcmu.com press release {year}",
            "Mauritius petrol diesel price {month} {year} MUR PPC official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._mur(t, ["Mogas","petrol","gasoline","motor spirit"], 40, 100)
        die = self._mur(t, ["Gas Oil","diesel","gasoil"], 40, 100)
        if not (gas and die): raise NoDataError("MUR prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _mur(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return MauritiusScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Mauritius: gas={r.gas_loc} MUR | die={r.die_loc} MUR | {r.effective_date}")

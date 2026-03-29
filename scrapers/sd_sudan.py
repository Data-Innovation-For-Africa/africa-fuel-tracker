"""Sudan — oilpricez.com (mep.gov.sd offline, conflict)  Currency: SDG"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_VARIABLE
from utils.base import NoDataError

class SudanScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Sudan","iso2":"SD","region":"North Africa","currency":"SDG",
        "update_cycle":CYCLE_VARIABLE,"price_range":(200,2000),
        "official_sources":[
            {"url":"https://oilpricez.com/sd/sudan-gasoline-price","name":"oilpricez.com Sudan Gasoline","confidence":"medium"},
            {"url":"https://oilpricez.com/sd/sudan-diesel-price","name":"oilpricez.com Sudan Diesel","confidence":"medium"},
            {"url":"https://www.thefuelprice.com/Fsd/en","name":"TheFuelPrice Sudan","confidence":"medium"},
        ],
        "search_queries":[
            "Sudan fuel price SDG pound per liter {year} official pump",
            "Sudan gasoline diesel price {year} SDG Khartoum official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = die = None
        if "gasoline" in url or "Fsd" in url:
            gas = self._find(t, ["gasoline","petrol","benzine"], 200, 2000)
        if "diesel" in url:
            die = self._find(t, ["diesel","gasoil"], 200, 2000)
        if not gas:
            gas = self._find(t, ["gasoline","petrol","benzine","1 Liter"], 200, 2000)
        if not die:
            die = self._find(t, ["diesel","gasoil"], 200, 2000)
        if not (gas and die): raise NoDataError("SDG prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _find(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{3,4}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        # Also look for "1 Liter Price = 630 SDG"
        m = re.search(r"1 Liter Price[^0-9]{{0,20}}?(\d{{3,4}})", t)
        if m:
            v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return SudanScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Sudan: gas={r.gas_loc} SDG | die={r.die_loc} SDG | {r.effective_date}")

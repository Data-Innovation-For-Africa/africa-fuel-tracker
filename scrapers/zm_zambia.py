"""Zambia — ERB (end of month)  Currency: ZMW"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_EOM
from utils.base import NoDataError

class ZambiaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Zambia","iso2":"ZM","region":"Southern Africa","currency":"ZMW",
        "update_cycle":CYCLE_MONTHLY_EOM,"price_range":(15,45),
        "official_sources":[
            {"url":"https://www.erb.org.zm/wp-content/uploads/PressStatements/CurrentFuelPumpPrices.pdf",
             "name":"ERB Zambia — Current Fuel Pump Prices PDF","confidence":"high"},
            {"url":"https://www.erb.org.zm/category/price-build-up/",
             "name":"ERB Zambia — Price Build-up","confidence":"high"},
            {"url":"https://www.erb.org.zm/","name":"ERB Zambia","confidence":"high"},
        ],
        "search_queries":[
            "Zambia ERB fuel price ZMW kwacha per liter {month} {year} official",
            "site:erb.org.zm pump prices {year}",
            "Zambia petrol diesel price {month} {year} ZMW ERB official",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._zmw(t, ["petrol","gasoline","Premium"], 15, 45)
        die = self._zmw(t, ["diesel","AGO"], 15, 45)
        if not (gas and die): raise NoDataError("ZMW prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _zmw(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{2}}\.?\d{{0,2}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return ZambiaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Zambia: gas={r.gas_loc} ZMW | die={r.die_loc} ZMW | {r.effective_date}")

"""Egypt — MOPNG/SIS quarterly committee  Currency: EGP"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_QUARTERLY
from utils.base import NoDataError

class EgyptScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Egypt","iso2":"EG","region":"North Africa","currency":"EGP",
        "update_cycle":CYCLE_QUARTERLY,"price_range":(10,60),
        "official_sources":[
            {"url":"https://www.sis.gov.eg/en/media-center","name":"SIS Egypt — Media Center","confidence":"high"},
            {"url":"https://www.sis.gov.eg/","name":"SIS Egypt","confidence":"high"},
        ],
        "search_queries":[
            "Egypt fuel price EGP pound per liter {month} {year} official MOPNG committee",
            "Egypt petrol diesel prices {year} EGP increase official announcement",
            "أسعار الوقود مصر {year} رسمي بنزين",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._find(t, ["gasoline","petrol","benzine","octane","بنزين"], 10, 60)
        die = self._find(t, ["diesel","gasoil","سولار"], 10, 60)
        if not (gas and die): raise NoDataError("EGP prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _find(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,60}}?(\d{{2,3}}\.?\d{{0,1}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return EgyptScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Egypt: gas={r.gas_loc} EGP | die={r.die_loc} EGP | {r.effective_date}")

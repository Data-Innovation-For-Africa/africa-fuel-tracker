"""Guinea — Min. Mines Hydrocarbures  Currency: GNF"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class GuineaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Guinea","iso2":"GN","region":"West Africa","currency":"GNF",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(8000,20000),
        "official_sources":[
            {"url":"https://www.mines.gov.gn/","name":"Min. Mines Hydrocarbures Guinée","confidence":"high"},
            {"url":"https://www.guineenews.org/","name":"GuineeNews — prix carburant","confidence":"medium"},
        ],
        "search_queries":[
            "Guinée prix carburant GNF franc guinéen litre {month} {year} officiel ministère",
            "Guinea fuel price GNF per liter {year} official mines",
            "prix essence gasoil Guinée Conakry GNF {year}",
        ],
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._gnf(t, ["essence","super","gasoline","benzine"], 8000, 20000)
        die = self._gnf(t, ["gasoil","diesel","gazole"], 8000, 20000)
        if not (gas and die): raise NoDataError("GNF prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _gnf(self, t, kws, mn, mx):
        for kw in kws:
            m = re.search(rf"(?i){kw}[^0-9]{{0,80}}?(\d{{4,6}})", t)
            if m:
                v=float(m.group(1)); return v if mn<=v<=mx else None
        return None
    def _date(self, t):
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return GuineaScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Guinea: gas={r.gas_loc} GNF | die={r.die_loc} GNF | {r.effective_date}")

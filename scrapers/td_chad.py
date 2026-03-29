"""Chad — Min. Finances Tchad  Currency: XAF"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY, CYCLE_QUARTERLY, CYCLE_STABLE
from utils.base import NoDataError

MONTHS_FR = {"janvier":"01","février":"02","mars":"03","avril":"04","mai":"05","juin":"06",
    "juillet":"07","août":"08","septembre":"09","octobre":"10","novembre":"11","décembre":"12"}

class ChadScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Chad","iso2":"TD","region":"Central Africa","currency":"XAF",
        "update_cycle":CYCLE_STABLE,"price_range":(400,1400),
        "official_sources":[
            {"url":"https://www.finances.gouv.td/","name":"Min. Finances Tchad","confidence":"high"},
            {"url":"https://www.finances.gouv.td/prix-carburants/","name":"Min. Finances Tchad alt","confidence":"high"},
        ],
        "search_queries":[
            "Chad prix carburant FCFA XAF litre {month} {year} officiel",
            "Chad fuel price XAF FCFA {year} official",
        ],
        "last_known":{"gas_loc":730,"die_loc":828,"date":"2024-02-01"},
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._xaf(t, ["supercarburant","super sans plomb","essence","SP","gasoline","petrol"])
        die = self._xaf(t, ["gasoil","gazole","diesel","gasoïl"])
        if not (gas and die):
            lk = self.COUNTRY_META["last_known"]
            return lk["gas_loc"], lk["die_loc"], lk["date"]
        return gas, die, self._date(t) or date.today().isoformat()
    def _xaf(self, t, kws):
        mn, mx = 400, 1400
        for kw in kws:
            m = re.search(rf"(?i){re.escape(kw)}[^0-9]{{0,60}}?(\d{{3,4}})", t)
            if m:
                v=float(m.group(1)); 
                if mn<=v<=mx: return v
        return None
    def _date(self, t):
        m=re.search(r"(\d{{1,2}})\s+("+ "|".join(MONTHS_FR.keys()) +r")\s+(\d{{4}})", t, re.IGNORECASE)
        if m: return f"{m.group(3)}-{MONTHS_FR.get(m.group(2).lower(),'01')}-{m.group(1).zfill(2)}"
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return ChadScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Chad: gas={r.gas_loc} XAF | die={r.die_loc} XAF | {r.effective_date}")

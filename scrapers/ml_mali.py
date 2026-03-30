"""Mali — Dir. Nationale Énergie Mali  Currency: XOF"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY, CYCLE_VARIABLE, CYCLE_STABLE
from utils.base import NoDataError

MONTHS_FR = {"janvier":"01","février":"02","mars":"03","avril":"04","mai":"05","juin":"06",
    "juillet":"07","août":"08","septembre":"09","octobre":"10","novembre":"11","décembre":"12"}

class MaliScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Mali","iso2":"ML","region":"West Africa","currency":"XOF",
        "update_cycle":CYCLE_MONTHLY_ANY,"price_range":(400,1200),
        "official_sources":[
            {"url":"https://www.energie.gov.ml/","name":"Dir. Nationale Énergie Mali","confidence":"high"},
            {"url":"https://www.energie.gov.ml/prix/","name":"Dir. Nationale Énergie Mali (fallback)","confidence":"high"},
        ],
        "search_queries":[
            "Mali prix carburant FCFA XOF litre {month} {year} officiel arrêté",
            "Mali fuel price XOF FCFA {year} official decree",
        ],
        "last_known":{"gas_loc":875,"die_loc":940,"date":"2026-03-28"},
    }
    def _parse(self, html, url):
        t = self._text(html)
        gas = self._xof(t, ["supercarburant","super sans plomb","essence","SP95","benzine","gasoline","petrol"])
        die = self._xof(t, ["gasoil","gazole","diesel","gasoïl"])
        if not (gas and die): raise NoDataError("XOF prices not found")
        return gas, die, self._date(t) or date.today().isoformat()
    def _xof(self, t, kws):
        for kw in kws:
            m = re.search(rf"(?i){re.escape(kw)}[^0-9]{{0,60}}?(\d{{3,4}})\s*(?:FCFA|CFA|F\s*CFA|XOF)", t)
            if m:
                v=float(m.group(1)); return v if 400<=v<=1200 else None
            m = re.search(rf"(?i)(\d{{3,4}})\s*(?:FCFA|CFA|XOF)[^.{{0,60}}]{re.escape(kw)}", t)
            if m:
                v=float(m.group(1)); return v if 400<=v<=1200 else None
        return None
    def _date(self, t):
        m=re.search(r"(\d{{1,2}})\s+("+ "|".join(MONTHS_FR.keys()) +r")\s+(\d{{4}})", t, re.IGNORECASE)
        if m: return f"{m.group(3)}-{MONTHS_FR.get(m.group(2).lower(),'01')}-{m.group(1).zfill(2)}"
        m=re.search(r"\b(\d{{4}}-\d{{2}}-\d{{2}})\b",t); return m.group(1) if m else None

def scrape(): return MaliScraper().run()
if __name__=="__main__":
    r=scrape(); print(f"Mali: gas={r.gas_loc} XOF | die={r.die_loc} XOF | {r.effective_date}")

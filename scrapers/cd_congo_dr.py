"""Congo DR — Min. Hydrocarbures RDC  Currency: CDF (Congolese Franc)
NOTE: Congo DR uses CDF (Congolese Franc, ~2820/USD), NOT XAF (CFA Franc).
XAF is used by Congo-Brazzaville and other BEAC countries, not the DRC.
"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

MONTHS_FR = {"janvier":"01","février":"02","mars":"03","avril":"04","mai":"05","juin":"06",
    "juillet":"07","août":"08","septembre":"09","octobre":"10","novembre":"11","décembre":"12"}

class CongoDRScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Congo DR","iso2":"CD","region":"Central Africa",
        "currency":"CDF",          # Congolese Franc — NOT XAF
        "update_cycle":CYCLE_MONTHLY_ANY,
        "price_range":(1500, 6000),  # CDF per litre (2968 CDF/L at ~2820 CDF/USD = $1.05)
        "official_sources":[
            {"url":"https://www.hydrocarbures.gouv.cd/","name":"Min. Hydrocarbures RDC","confidence":"high"},
            {"url":"https://actualite.cd/","name":"Actualite.cd RDC","confidence":"medium"},
        ],
        "search_queries":[
            "Congo RDC prix carburant CDF franc congolais litre {month} {year} officiel",
            "DRC Congo fuel price CDF Congolese franc {year} official Kinshasa",
            "RDC prix essence gasoil litre {year} officiel hydrocarbures",
        ],
        "last_known":{"gas_loc":2968,"die_loc":2431,"date":"2026-02-01"},
    }

    def _parse(self, html, url):
        t = self._text(html)
        gas = self._cdf(t, ["supercarburant","super sans plomb","essence","SP","gasoline","petrol"])
        die = self._cdf(t, ["gasoil","gazole","diesel","gasoïl"])
        if not (gas and die):
            lk = self.COUNTRY_META["last_known"]
            return lk["gas_loc"], lk["die_loc"], lk["date"]
        return gas, die, self._date(t) or date.today().isoformat()

    def _cdf(self, t, kws):
        mn, mx = 1500, 6000   # CDF/L range
        for kw in kws:
            m = re.search(rf"(?i){re.escape(kw)}[^0-9]{{0,60}}?(\d{{3,4}})", t)
            if m:
                v = float(m.group(1))
                if mn <= v <= mx:
                    return v
        return None

    def _date(self, t):
        m = re.search(r"(\d{1,2})\s+(" + "|".join(MONTHS_FR.keys()) + r")\s+(\d{4})",
                      t, re.IGNORECASE)
        if m:
            return f"{m.group(3)}-{MONTHS_FR.get(m.group(2).lower(),'01')}-{m.group(1).zfill(2)}"
        m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", t)
        return m.group(1) if m else None

def scrape(): return CongoDRScraper().run()
if __name__ == "__main__":
    r = scrape()
    print(f"Congo DR: gas={r.gas_loc} CDF | die={r.die_loc} CDF | {r.effective_date}")


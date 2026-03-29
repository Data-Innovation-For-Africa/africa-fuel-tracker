"""Nigeria — NNPC Limited (deregulated market)  Currency: NGN"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_WEEKLY
from utils.base import NoDataError

class NigeriaScraper(SmartScraper):
    COUNTRY_META = {
        "country":"Nigeria","iso2":"NG","region":"West Africa","currency":"NGN",
        "update_cycle":CYCLE_WEEKLY,
        # NGN real range: 600–2500 NGN/L — but 2026 must be excluded
        # Use explicit lower-bound patterns to avoid matching year "2026"
        "price_range":(600, 2500),
        "official_sources":[
            {"url":"https://www.nnpcgroup.com/","name":"NNPC Limited Nigeria","confidence":"high"},
            {"url":"https://www.nnpcgroup.com/NNPC-Business/Downstream-Ventures/Pages/Retail.aspx","name":"NNPC Retail","confidence":"high"},
            {"url":"https://nnpcretail.com/","name":"NNPC Retail Prices","confidence":"high"},
        ],
        "search_queries":[
            "Nigeria NNPC fuel price NGN naira per liter {month} {year} Lagos official",
            "Nigeria petrol diesel price {month} {year} NGN official NNPC",
            "Nigeria fuel price increase {year} naira liter NNPC",
        ],
    }

    def _parse(self, html, url):
        t = self._text(html)
        gas = self._ngn(t, ["petrol","PMS","Premium Motor Spirit","gasoline"])
        die = self._ngn(t, ["diesel","AGO","Automotive Gas"])
        if not (gas and die): raise NoDataError("NGN prices not found")
        return gas, die, self._date(t) or date.today().isoformat()

    def _ngn(self, t, kws):
        mn, mx = 600, 2500
        for kw in kws:
            # Find keyword then scan ahead for a valid NGN price
            # Exclude 4-digit years (2020-2029, 2010-2019) explicitly
            m = re.search(
                rf"(?i){kw}[^0-9]{{0,120}}?"
                rf"(?<!\d)"                             # not preceded by digit
                rf"(?!20[12]\d\b)"                     # not a year like 2026
                rf"((?:1[0-9]{{3}}|2[0-4]\d{{2}}|[6-9]\d{{2}})(?:\.\d{{1,2}})?)"
                rf"(?!\d)",                             # not followed by digit
                t
            )
            if m:
                v = float(m.group(1))
                if mn <= v <= mx:
                    return v
            # Secondary: ₦ or NGN symbol near a number
            m2 = re.search(
                r"(?:₦|NGN)\s*((?:1[0-9]{3}|2[0-4]\d{2}|[6-9]\d{2})(?:\.\d{1,2})?)",
                t
            )
            if m2:
                v = float(m2.group(1))
                if mn <= v <= mx:
                    return v
        return None

    def _date(self, t):
        m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", t)
        return m.group(1) if m else None

def scrape(): return NigeriaScraper().run()
if __name__ == "__main__":
    r = scrape()
    print(f"Nigeria: gas={r.gas_loc} NGN | die={r.die_loc} NGN | {r.effective_date}")


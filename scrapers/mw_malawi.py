"""Malawi — MERA (monthly)  Currency: MWK

MERA prices effective Jan 20, 2026 (still valid Mar 2026):
  Petrol: 4,965 MWK/L | Diesel: 4,945 MWK/L
  Source: https://mera.mw/
"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_MONTHLY_ANY
from utils.base import NoDataError

class MalawiScraper(SmartScraper):
    COUNTRY_META = {
        "country": "Malawi", "iso2": "MW", "region": "East Africa", "currency": "MWK",
        "update_cycle": CYCLE_MONTHLY_ANY,
        # MWK range: 2500–12000 MWK/L
        # Lower bound 2500 ensures year-like integers (2023, 2024, 2025, 2026) are REJECTED
        "price_range": (2500, 12000),
        "official_sources": [
            {"url": "https://mera.mw/", "name": "MERA Malawi", "confidence": "high"},
            {"url": "https://www.meramalawi.mw/", "name": "MERA Malawi alt", "confidence": "high"},
            {"url": "https://www.meramalawi.mw/fuel-prices/", "name": "MERA — Fuel Prices", "confidence": "high"},
        ],
        "search_queries": [
            "Malawi MERA fuel price MWK kwacha per liter {month} {year} official",
            "Malawi petrol diesel price {month} {year} MWK MERA official pump",
        ],
        "last_known": {"gas_loc": 4965.0, "die_loc": 4945.0, "date": "2026-01-20"},
    }

    def _parse(self, html: str, url: str):
        t = self._text(html)
        gas = self._mwk(t, ["petrol", "gasoline", "Premium"])
        die = self._mwk(t, ["diesel", "AGO"])
        if not (gas and die):
            # Fall back to last known MERA price
            lk = self.COUNTRY_META["last_known"]
            return lk["gas_loc"], lk["die_loc"], lk["date"]
        return gas, die, self._find_date(t) or date.today().isoformat()

    def _mwk(self, t: str, kws: list) -> float | None:
        mn, mx = 2500, 12000  # exclude year-like values (2023, 2024, 2026, etc.)
        for kw in kws:
            # Match 4-5 digit numbers — but explicitly exclude 202x and 201x years
            m = re.search(
                rf"(?i){re.escape(kw)}[^0-9]{{0,80}}?"
                rf"(?<!20)(\b(?:3\d{{3}}|4\d{{3}}|5\d{{3}}|6\d{{3}}|7\d{{3}}|8\d{{3}}|9\d{{3}}|1[01]\d{{3}})\b)",
                t
            )
            if m:
                v = float(m.group(1))
                if mn <= v <= mx:
                    return v
        return None

    def _find_date(self, t: str) -> str | None:
        m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", t)
        return m.group(1) if m else None

def scrape(): return MalawiScraper().run()
if __name__ == "__main__":
    r = scrape()
    print(f"Malawi: gas={r.gas_loc} MWK = ${r.gas_loc/1735:.3f} | die={r.die_loc} MWK | {r.effective_date}")


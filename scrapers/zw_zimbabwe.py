"""Zimbabwe — ZERA (weekly)  Currency: ZWG

Real ZWG pump prices (ZERA official):
  Mar 2026: ~56 ZWG/L petrol at ZWG/USD ~26 → ~$2.17/L
  Upper bound set at 120 ZWG/L to guard against regex false-positives.
  Value 154 that was captured previously is NOT a ZERA pump price —
  it likely came from a page cost/tax breakdown figure.
"""
import re, sys
from pathlib import Path
from datetime import date
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.smart_scraper import SmartScraper, CYCLE_WEEKLY
from utils.base import NoDataError


class ZimbabweScraper(SmartScraper):
    COUNTRY_META = {
        "country": "Zimbabwe", "iso2": "ZW", "region": "Southern Africa", "currency": "ZWG",
        "update_cycle": CYCLE_WEEKLY,
        # ZERA real prices: ~40–120 ZWG/L (=$1.5–$4.6 at 26 ZWG/USD)
        # Max capped at 120 to reject false-positive page numbers like 154, 2026, etc.
        "price_range": (30, 120),
        "official_sources": [
            {"url": "https://www.zera.co.zw/", "name": "ZERA Zimbabwe", "confidence": "high"},
            {"url": "https://www.zera.co.zw/fuel-prices/", "name": "ZERA — Fuel Prices", "confidence": "high"},
        ],
        "search_queries": [
            "Zimbabwe ZERA fuel price ZWG per liter {month} {year} official Harare",
            "site:zera.co.zw fuel prices {year}",
            "Zimbabwe petrol diesel pump price {month} {year} ZWG ZERA official",
        ],
    }

    def _parse(self, html: str, url: str):
        t = self._text(html)
        gas = self._zwg(t, ["petrol", "gasoline", "Premium", "unleaded"])
        die = self._zwg(t, ["diesel", "AGO", "gasoil"])
        if not (gas and die):
            raise NoDataError("ZWG prices not found")
        return gas, die, self._find_date(t) or date.today().isoformat()

    def _zwg(self, t: str, kws: list) -> float | None:
        mn, mx = 30, 120
        for kw in kws:
            # Look for 2-digit price (30–99) right after the keyword
            # Avoids 3-digit numbers that could be page artefacts (154, 2026, etc.)
            m = re.search(
                rf"(?i){re.escape(kw)}[^0-9]{{0,80}}?"
                rf"(\b(?:[3-9]\d|1[01]\d)\b(?:\.\d{{1,2}})?)",
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


def scrape():
    return ZimbabweScraper().run()


if __name__ == "__main__":
    r = scrape()
    print(f"Zimbabwe: gas={r.gas_loc} ZWG | die={r.die_loc} ZWG | {r.effective_date}")



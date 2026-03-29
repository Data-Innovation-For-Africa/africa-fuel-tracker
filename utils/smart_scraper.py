"""
utils/smart_scraper.py — Base class for all 54 intelligent country scrapers

Every scraper inherits SmartScraper and implements:
  - COUNTRY_META  : dict with all metadata
  - _parse(html, url) : extract (gas_loc, die_loc, effective_date) from HTML

The intelligence logic (fallback chain + DuckDuckGo) lives here.
"""
import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .base import CountryResult, ScraperError, NoDataError
from .search import search, fetch_page, extract_prices_from_text

# Update cycle constants
CYCLE_DAILY       = "daily"         # every day (Uganda PAU, Zimbabwe ZERA)
CYCLE_WEEKLY      = "weekly"        # every week (Morocco, Nigeria)
CYCLE_BIMONTHLY   = "bimonthly"     # twice a month (Ghana, Rwanda, Burundi)
CYCLE_MONTHLY_1   = "monthly_1"     # 1st of each month
CYCLE_MONTHLY_15  = "monthly_15"    # 15th of each month (Kenya EPRA)
CYCLE_MONTHLY_EOM = "monthly_eom"   # end of month (Zambia ERB)
CYCLE_MONTHLY_ANY = "monthly"       # monthly but variable day
CYCLE_QUARTERLY   = "quarterly"     # every 3 months
CYCLE_STABLE      = "stable"        # rarely changes (Libya, Tunisia, Angola…)
CYCLE_VARIABLE    = "variable"      # no fixed pattern (Somalia, South Sudan…)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/122 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
}


class SmartScraper(ABC):
    """
    Base class for a smart country scraper.

    Subclasses define COUNTRY_META and implement _parse().
    The run() method handles the full fallback chain automatically.
    """

    # ── Must be defined in each subclass ────────────────────────────────────
    COUNTRY_META: dict = {}

    # ── Fallback chain ────────────────────────────────────────────────────────
    def run(self) -> CountryResult:
        """
        Full intelligent scraping pipeline:
        1. Try each official URL in order
        2. If all fail → DuckDuckGo search + fetch top results
        3. If still nothing → raise ScraperError
        """
        meta = self.COUNTRY_META
        country  = meta["country"]
        currency = meta["currency"]
        min_v, max_v = meta["price_range"]

        # ── Step 1: Try predefined official sources ──────────────────────────
        for source in meta.get("official_sources", []):
            url      = source["url"]
            src_name = source["name"]
            conf     = source.get("confidence", "high")

            html = _fetch(url)
            if html is None:
                print(f"    [{country}] ✗ {url[:55]}")
                continue

            try:
                gas, die, eff_date = self._parse(html, url)
                if gas and die and min_v <= gas <= max_v and min_v <= die <= max_v:
                    print(f"    [{country}] ✓ {src_name}")
                    return self._build_result(gas, die, eff_date, url, src_name, conf)
            except Exception as e:
                print(f"    [{country}] parse error on {url[:50]}: {e}")
                continue

        # ── Step 2: DuckDuckGo search fallback ───────────────────────────────
        today = date.today()
        for query_tpl in meta.get("search_queries", []):
            query = query_tpl.format(
                year=today.year,
                month=today.strftime("%B"),
                month_num=today.month,
                currency=currency,
                country=country,
            )
            print(f"    [{country}] 🔍 search: {query[:70]}")
            results = search(query, max_results=6)

            for result in results:
                html = fetch_page(result.url)
                if html is None:
                    continue
                try:
                    gas, die, eff_date = self._parse(html, result.url)
                    if gas and die and min_v <= gas <= max_v and min_v <= die <= max_v:
                        print(f"    [{country}] ✓ (via search) {result.domain}")
                        return self._build_result(
                            gas, die, eff_date,
                            result.url, result.domain,
                            confidence="medium"   # secondary source
                        )
                except Exception:
                    # Generic extraction as last resort
                    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
                    gas, die = extract_prices_from_text(text, currency, min_v, max_v)
                    if gas and die:
                        eff_date = _extract_any_date(text) or today.isoformat()
                        print(f"    [{country}] ✓ (generic parse) {result.domain}")
                        return self._build_result(
                            gas, die, eff_date,
                            result.url, result.domain,
                            confidence="medium"
                        )

        raise ScraperError(
            f"[{country}] All sources failed — no price found from official URLs or DuckDuckGo"
        )

    # ── To implement in each subclass ────────────────────────────────────────
    @abstractmethod
    def _parse(self, html: str, url: str) -> tuple[float, float, str]:
        """
        Extract (gas_loc, die_loc, effective_date) from the HTML of a given URL.
        Must raise NoDataError if the expected data is not found on this page.
        effective_date format: YYYY-MM-DD
        """
        ...

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _build_result(
        self,
        gas: float, die: float, eff_date: str,
        url: str, source_name: str,
        confidence: str = "high",
    ) -> CountryResult:
        meta = self.COUNTRY_META
        old_source = meta.get("old_source", False)
        if old_source:
            confidence = "low"
        return CountryResult(
            country        = meta["country"],
            iso2           = meta["iso2"],
            region         = meta["region"],
            currency       = meta["currency"],
            gas_loc        = round(float(gas), 4),
            die_loc        = round(float(die), 4),
            source_url     = url,
            source_name    = source_name,
            effective_date = eff_date or date.today().isoformat(),
            old_source     = old_source,
            confidence     = confidence,
        )

    def _soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def _text(self, html: str) -> str:
        return re.sub(r"\s+", " ", BeautifulSoup(html, "lxml").get_text(" ", strip=True))


# ── Module-level helpers ─────────────────────────────────────────────────────

def _fetch(url: str, timeout: int = 20) -> str | None:
    """Fetch URL, return HTML text or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def _extract_any_date(text: str) -> str | None:
    """Try to extract any ISO or readable date from text."""
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if m:
        return m.group(1)
    months = {
        "january":"01","february":"02","march":"03","april":"04",
        "may":"05","june":"06","july":"07","august":"08",
        "september":"09","october":"10","november":"11","december":"12",
        "janvier":"01","février":"02","mars":"03","avril":"04",
        "mai":"05","juin":"06","juillet":"07","août":"08",
        "septembre":"09","octobre":"10","novembre":"11","décembre":"12",
    }
    m = re.search(
        r"(\d{1,2})\s+(" + "|".join(months) + r")\s+(\d{4})",
        text, re.IGNORECASE
    )
    if m:
        day, mon, yr = m.group(1), m.group(2).lower(), m.group(3)
        return f"{yr}-{months[mon]}-{day.zfill(2)}"
    return None


def parse_number(text: str) -> float | None:
    """Parse a number string like '178.28' or '1,989' into float."""
    clean = re.sub(r"[^\d.]", "", text.replace(",", "."))
    try:
        return float(clean)
    except ValueError:
        return None

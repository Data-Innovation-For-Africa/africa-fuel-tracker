"""
utils/search.py — DuckDuckGo HTML search for Africa Fuel Tracker

Uses the DuckDuckGo HTML endpoint (no API key, no rate-limit headers needed).
Returns a list of SearchResult with url, title, snippet.

Used as fallback when all predefined scraper URLs fail.
"""
import re
import time
import random
import requests
from dataclasses import dataclass
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urlparse

DDG_URL = "https://html.duckduckgo.com/html/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Referer": "https://duckduckgo.com/",
}

# Domains to skip (aggregators, estimated data, GPP explicitly blocked)
BLOCKED_DOMAINS = {
    "globalpetrolprices.com",
    "numbeo.com",
    "statista.com",
    "tradingeconomics.com",  # uses estimates
    "knoema.com",
    "indexmundi.com",
    "quora.com",
    "reddit.com",
    "wikipedia.org",
}


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str
    domain: str


def search(query: str, max_results: int = 8) -> list[SearchResult]:
    """
    Search DuckDuckGo HTML and return a list of SearchResult.
    Filters out blocked domains and returns up to max_results.
    """
    # Small random delay to be polite and avoid rate limits
    time.sleep(random.uniform(1.0, 2.5))

    try:
        params = {"q": query, "kl": "wt-wt", "kp": "-1", "kaf": "1"}
        resp = requests.post(
            DDG_URL,
            data=params,
            headers=HEADERS,
            timeout=20,
            allow_redirects=True,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"    [search] DuckDuckGo request failed: {e}")
        return []

    return _parse_results(resp.text, max_results)


def _parse_results(html: str, max_results: int) -> list[SearchResult]:
    soup = BeautifulSoup(html, "lxml")
    results = []

    for div in soup.select("div.result, div.results_links_deep"):
        # Extract URL
        link = div.select_one("a.result__url, a.result__a")
        if not link:
            continue

        raw_url = link.get("href", "").strip()
        if not raw_url or raw_url.startswith("//duckduckgo"):
            continue

        # Clean DDG redirect URLs
        if "uddg=" in raw_url:
            m = re.search(r"uddg=([^&]+)", raw_url)
            if m:
                from urllib.parse import unquote
                raw_url = unquote(m.group(1))

        if not raw_url.startswith("http"):
            raw_url = "https://" + raw_url

        domain = urlparse(raw_url).netloc.replace("www.", "").lower()

        # Skip blocked domains
        if any(blocked in domain for blocked in BLOCKED_DOMAINS):
            continue

        title   = (div.select_one("a.result__a, h2") or link).get_text(strip=True)
        snippet = (div.select_one("a.result__snippet, .result__body") or div).get_text(
            " ", strip=True
        )[:300]

        results.append(SearchResult(
            url=raw_url, title=title, snippet=snippet, domain=domain
        ))

        if len(results) >= max_results:
            break

    return results


def fetch_page(url: str, timeout: int = 20) -> str | None:
    """Fetch a URL and return its text. Returns None on any error."""
    time.sleep(random.uniform(0.5, 1.5))
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"    [fetch] {url} → {type(e).__name__}: {e}")
        return None


def extract_prices_from_text(
    text: str,
    currency: str,
    min_val: float,
    max_val: float,
) -> tuple[float | None, float | None]:
    """
    Generic price extraction from arbitrary text.
    Looks for (gasoline/petrol/essence, diesel/gasoil) price patterns near `currency`.
    Returns (gas_price, diesel_price) or (None, None).
    """
    # Normalise text
    t = re.sub(r"\s+", " ", text)

    gas = _find_price_near_keyword(t, ["gasoline", "petrol", "benzine", "essence", "PMS", "SP95"], min_val, max_val)
    die = _find_price_near_keyword(t, ["diesel", "gasoil", "AGO", "gasoleo", "gazole"], min_val, max_val)

    return gas, die


def _find_price_near_keyword(
    text: str, keywords: list[str], min_val: float, max_val: float
) -> float | None:
    """Find a numeric value near any keyword, within valid range."""
    # Year integers to exclude (e.g. "2026", "2025")
    YEAR_RE = re.compile(r"^20\d\d$")

    def is_year(raw: str) -> bool:
        return bool(YEAR_RE.match(raw.strip()))

    for kw in keywords:
        # Find all positions of keyword in text
        for kw_match in re.finditer(rf"(?i){re.escape(kw)}", text):
            pos = kw_match.end()
            # Scan all numbers in the next 200 characters
            window = text[pos:pos + 200]
            for num_match in re.finditer(r"([\d][\d.,]{0,10})", window):
                raw = num_match.group(1).replace(",", "").rstrip(".")
                if is_year(raw):
                    continue
                try:
                    val = float(raw)
                    if min_val <= val <= max_val:
                        return val
                except ValueError:
                    continue
        # Also try: number BEFORE keyword
        for num_match in re.finditer(r"([\d][\d.,]{0,10})", text):
            raw = num_match.group(1).replace(",", "").rstrip(".")
            if is_year(raw):
                continue
            num_end = num_match.end()
            # Check if keyword appears within 100 chars after this number
            after = text[num_end:num_end + 100]
            if re.search(rf"(?i){re.escape(kw)}", after):
                try:
                    val = float(raw)
                    if min_val <= val <= max_val:
                        return val
                except ValueError:
                    continue
    return None

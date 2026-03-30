"""
Base scraper class and shared types for Africa Fuel Tracker.
Every country scraper must implement the scrape() function
returning a CountryResult dict or raising ScraperError.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


class ScraperError(Exception):
    """Raised when a scraper cannot retrieve valid data."""
    pass


class NoDataError(ScraperError):
    """Raised when the source exists but contains no parseable price."""
    pass


@dataclass
class CountryResult:
    """
    Standardised output from every country scraper.
    All fields except gas_loc/die_loc are required.
    """
    country: str
    iso2: str
    region: str
    currency: str

    gas_loc: float          # gasoline price in local currency
    die_loc: float          # diesel price in local currency

    source_url: str         # exact URL scraped
    source_name: str        # human label e.g. "EPRA Kenya"
    effective_date: str     # date the price is officially valid (YYYY-MM-DD)

    # Set automatically by orchestrator — do not set in scraper
    gas_usd: float = 0.0
    die_usd: float = 0.0
    fx_rate: float = 0.0
    fx_source: str = ""
    fx_date: str = ""
    scraped_at: str = ""
    status: str = "ok"
    stale: bool = False
    old_source: bool = False    # True for Eritrea (data from 2016)
    confidence: str = "medium"  # "high" | "medium" | "low"
    delta_gas_usd: float = 0.0
    delta_die_usd: float = 0.0

    def to_dict(self) -> dict:
        return {
            "iso2": self.iso2,
            "region": self.region,
            "currency": self.currency,
            "gas_loc": round(self.gas_loc, 4),
            "die_loc": round(self.die_loc, 4),
            "gas_usd": round(self.gas_usd, 4),
            "die_usd": round(self.die_usd, 4),
            "fx_rate": round(self.fx_rate, 4),
            "fx_source": self.fx_source,
            "fx_date": self.fx_date,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "effective_date": self.effective_date,
            "scraped_at": self.scraped_at,
            "status": self.status,
            "stale": self.stale,
            "old_source": self.old_source,
            "confidence": self.confidence,
            "delta_gas_usd": round(self.delta_gas_usd, 4),
            "delta_die_usd": round(self.delta_die_usd, 4),
        }


# Validation ranges — gas_loc must fall within these bounds
# Format: "ISO2": (currency, min_local, max_local)
PRICE_RANGES = {
    "DZ": ("DZD", 30, 80),
    "EG": ("EGP", 10, 50),
    "LY": ("LYD", 0.05, 1.0),
    "MA": ("MAD", 8, 20),
    "SD": ("SDG", 200, 1500),
    "TN": ("TND", 1.5, 4.0),
    "BJ": ("XOF", 500, 1200),
    "BF": ("XOF", 500, 1100),
    "CV": ("CVE", 80, 180),
    "GM": ("GMD", 40, 120),
    "GH": ("GHS", 8, 25),
    "GN": ("GNF", 8000, 18000),
    "GW": ("XOF", 500, 1100),
    "CI": ("XOF", 500, 1100),
    "LR": ("LRD", 100, 300),
    "ML": ("XOF", 500, 1100),
    "MR": ("MRU", 25, 70),
    "NE": ("XOF", 400, 800),
    "NG": ("NGN", 600, 2000),
    "SN": ("XOF", 600, 1200),
    "SL": ("SLL", 20000, 50000),
    "TG": ("XOF", 500, 1100),
    "CF": ("XAF", 600, 1800),
    "CM": ("XAF", 600, 1200),
    "TD": ("XAF", 500, 1200),
    "CD": ("CDF", 1500, 6000),
    "CG": ("XAF", 500, 1100),
    "GQ": ("XAF", 300, 900),
    "GA": ("XAF", 400, 900),
    "ST": ("STN", 18, 45),
    "BI": ("BIF", 2000, 6000),
    "KM": ("KMF", 400, 1000),
    "DJ": ("DJF", 150, 350),
    "ER": ("ERN", 10, 60),
    "ET": ("ETB", 80, 200),
    "KE": ("KES", 130, 230),
    "MG": ("MGA", 3500, 8000),
    "MW": ("MWK", 2000, 8000),
    "MU": ("MUR", 40, 90),
    "RW": ("RWF", 1200, 2500),
    "SC": ("SCR", 12, 30),
    "SO": ("USD", 0.5, 2.5),
    "SS": ("SSP", 1000, 60000),
    "TZ": ("TZS", 2000, 4000),
    "UG": ("UGX", 3000, 7000),
    "AO": ("AOA", 150, 600),
    "BW": ("BWP", 10, 35),
    "SZ": ("SZL", 15, 30),
    "LS": ("LSL", 15, 28),
    "MZ": ("MZN", 50, 130),
    "NA": ("NAD", 15, 28),
    "ZA": ("ZAR", 15, 28),
    "ZM": ("ZMW", 15, 35),
    "ZW": ("ZWG", 30, 120),
}


def validate_price(iso2: str, gas_loc: float, die_loc: float) -> bool:
    """Return True if both prices are within expected range."""
    if iso2 not in PRICE_RANGES:
        return True  # no range defined, accept
    _, min_v, max_v = PRICE_RANGES[iso2]
    return (min_v <= gas_loc <= max_v) and (min_v <= die_loc <= max_v)

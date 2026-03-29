# ⛽ Africa Fuel Price Tracker

> Real-time fuel price intelligence across all 54 African nations — automatically updated every day at 05:00 UTC.

[![Daily Update](https://github.com/Data-Innovation-For-Africa/africa-fuel-tracker/actions/workflows/daily_update.yml/badge.svg)](https://github.com/Data-Innovation-For-Africa/africa-fuel-tracker/actions/workflows/daily_update.yml)

## 🌐 Live Dashboard

**→ [Open Dashboard](https://data-innovation-for-africa.github.io/africa-fuel-tracker/)**

---

## What it tracks

| | |
|---|---|
| **Countries** | 54 African nations (all AU members) |
| **Regions** | North · West · East · Central · Southern Africa |
| **Fuel types** | Gasoline · Diesel |
| **Currencies** | USD/L + local national currency/L (41 currencies) |
| **Period** | January 2026 → present |
| **Update** | Every day at 05:00 UTC (GitHub Actions) |

## Dashboard features

- 📈 Weekly trend chart — Key markets (toggle Gas USD / Local / Diesel)
- 🗺️ Regional average cards (5 regions) with Jan→Now change
- 🏆 Top 10 most expensive / most affordable (toggle USD / Local)
- 💱 All exchange rates (official central bank references)
- 🔍 Search · filter by region · sort by price / change
- 📋 Full 54-country table (USD / local / both modes)
- 🖱️ Click any country → detailed modal with dual-axis history chart
- 📥 Export CSV

## Data sources

- Official national energy regulators (EPRA, EWURA, ZERA, DMRE, ERB, NPA, RURA, PAU, MERA, STC…)
- Government decrees (BCEAO/UEMOA, Primature Sénégal, Min. Énergie…)
- FX rates: [Frankfurter API](https://api.frankfurter.app) (ECB / central bank references)

## Architecture

```
africa-fuel-tracker/
├── scrapers/          # 54 country scrapers (1 per country)
├── utils/             # FX, DB, search, base classes
├── data/
│   ├── prices_db.json    # Current prices (updated daily)
│   └── history_db.json   # Price history (Jan 2026 → today)
├── generate_dashboard.py # Builds index.html from JSON data
├── run_all_scrapers.py   # Orchestrator (runs all 54 scrapers)
└── .github/workflows/
    └── daily_update.yml  # Runs daily at 05:00 UTC
```

## How it works

Each morning at 05:00 UTC, GitHub Actions:
1. Runs all 54 country scrapers sequentially
2. Each scraper tries official URLs, then falls back to DuckDuckGo search
3. Updates `data/prices_db.json` and appends to `data/history_db.json`
4. Regenerates `index.html` from the updated data
5. Commits and pushes — dashboard updates automatically

---

*No server required — pure static site hosted on GitHub Pages.*

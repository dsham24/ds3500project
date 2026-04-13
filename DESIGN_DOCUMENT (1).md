# Design Document: Housing Market & Affordability Dashboard

## 1. Domain & Motivation

Housing affordability is one of the most pressing economic issues in the United States. Home prices have surged in recent years while wages have grown more slowly, making homeownership increasingly out of reach for many Americans. This project builds an interactive dashboard that integrates multiple data sources to explore the relationship between home prices, mortgage rates, household income, and regional differences in housing affordability.

## 2. Research Questions

1. **How has housing affordability changed over time across U.S. states?** (Comparing home prices to household income)
2. **What is the relationship between mortgage rates and home prices?** (Do prices respond to rate changes?)
3. **Which states are the most and least affordable for homebuyers?** (Price-to-income ratios by state)
4. **How did major economic events (2008 crisis, COVID-19) impact housing markets differently across regions?**

## 3. Data Sources

| # | Source | Type | Key Data | Geographic Level | Frequency | API Key Required |
|---|--------|------|----------|-----------------|-----------|-----------------|
| 1 | FRED API | REST API | Median home price, mortgage rates, housing starts, Case-Shiller index, homeownership rate | National | Weekly/Monthly/Quarterly | Yes (free) |
| 2 | Census Bureau API | REST API | Median household income, median home value, rent, population, housing units by tenure | State | Annual (ACS 5-year) | Yes (free) |
| 3 | Zillow ZHVI CSV | Static CSV | Zillow Home Value Index — typical home value over time | State | Monthly | No |

**API Documentation & Registration:**
- FRED: https://fred.stlouisfed.org/docs/api/fred/ — key at https://fred.stlouisfed.org/docs/api/api_key.html (rate limit: 120 req/min)
- Census: https://www.census.gov/data/developers/data-sets.html — key at https://api.census.gov/data/key_signup.html (rate limit: 500 req/day without key)
- Zillow: https://www.zillow.com/research/data/ — no key required, direct CSV download

See `DATA_SOURCES.md` for complete field descriptions, access notes, and known data quality issues.

## 4. Key Fields & Data Dictionary

### FRED (national level, date-indexed)
| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `date` | Observation date | datetime | Frequency varies by series |
| `MSPUS` | Median sales price of houses sold | float (USD) | Quarterly; missing quarters = NaN |
| `MORTGAGE30US` | 30-year fixed mortgage rate | float (%) | Weekly; most granular series |
| `HOUST` | New privately-owned housing starts | float (thousands) | Monthly |
| `CSUSHPINSA` | Case-Shiller national home price index | float (index) | Monthly, not seasonally adjusted |
| `RHORUSQ156N` | National homeownership rate | float (%) | Quarterly |
| `MSACSR` | Monthly supply of houses | float (months) | Monthly |

### Census ACS 5-Year Estimates (state level, annual)
| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `state_name` | Full state name | string | Join key for Zillow merge |
| `state_fips` | 2-digit FIPS code | string | e.g., "06" for California |
| `year` | ACS vintage year | int | 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2023 |
| `median_household_income` | Median HH income | float (USD) | -666666666 = suppressed data |
| `median_home_value` | Median owner-occupied home value | float (USD) | |
| `median_gross_rent` | Median gross rent | float (USD) | |
| `homeownership_rate` | % owner-occupied of all occupied units | float (%) | Derived column |
| `price_to_income_ratio` | median_home_value / median_household_income | float | Derived column |

### Zillow ZHVI (state level, monthly)
| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `RegionName` | State name | string | Join key for Census merge |
| `date` | Month of observation | datetime | Monthly frequency |
| `zhvi` | Zillow Home Value Index | float (USD) | Smoothed, seasonally adjusted; 35th–65th percentile range |

## 5. Merge Strategy

**Primary join keys:**
- **Census ↔ Zillow:** `RegionName` (Zillow) matched to `state_name` (Census) + `year` — both datasets have state-level geography. Note: Zillow's `StateName` column is unpopulated in the raw CSV, so we join on `RegionName` directly. Zillow monthly data will be aggregated to annual averages to match ACS annual estimates.
- **FRED ↔ merged state data:** `year` (or `quarter`) — FRED national data provides macro context. National mortgage rates and price indices apply uniformly across states for a given time period.

**Final merged dataset structure:**
Each row = one state in one year, with columns for: income, home value (Census), ZHVI (Zillow), mortgage rate (FRED, national), home price index (FRED, national), and derived affordability metrics.

**Derived columns:**
- `price_to_income_ratio` = median_home_value / median_household_income
- `monthly_mortgage_payment` = estimated from median home value + mortgage rate
- `affordability_index` = income-based measure of whether median family can afford median home

## 6. Proposed Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   DATA ACQUISITION                       │
│                                                          │
│  ┌──────────┐   ┌──────────────┐   ┌───────────────┐   │
│  │ FRED API │   │ Census API   │   │ Zillow CSV    │   │
│  │ (fetch_  │   │ (fetch_      │   │ (fetch_       │   │
│  │  fred.py)│   │  census.py)  │   │  zillow.py)   │   │
│  └────┬─────┘   └──────┬───────┘   └──────┬────────┘   │
│       │                │                    │            │
│       ▼                ▼                    ▼            │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Raw CSV Files (data/)                │   │
│  └──────────────────────┬───────────────────────────┘   │
└─────────────────────────┼───────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────┐
│                DATA PROCESSING                           │
│                         ▼                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  clean.py — Handle missing values, standardize   │   │
│  │  types, remove duplicates, validate ranges       │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         ▼                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  merge.py — Join datasets on state + year,       │   │
│  │  compute derived affordability metrics           │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         ▼                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Cleaned & merged dataset (data/merged.parquet)  │   │
│  └──────────────────────┬───────────────────────────┘   │
└─────────────────────────┼───────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────┐
│                VISUALIZATION & DASHBOARD                 │
│                         ▼                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  dashboard.py (Panel)                            │   │
│  │  - Overview: National trends (prices, rates)     │   │
│  │  - Drill-down: State-level affordability         │   │
│  │  - Animated: Price changes over time             │   │
│  │  - Plotly: Interactive charts                    │   │
│  │  - Widgets: State selector, year slider, etc.    │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Docker container for deployment                 │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

## 7. Team Roles

- **Data Acquisition Lead (Zaid):** API integration, fetching scripts (`fetch_fred.py`, `fetch_census.py`, `fetch_zillow.py`), error handling, rate limit management, and sample data validation
- **Data Engineering Lead:** Cleaning pipeline (`clean.py`), merge logic (`merge.py`), handling missing values and type mismatches across sources, pytest test suite
- **Visualization Lead:** Dashboard design (`dashboard.py`), Plotly charts, Panel widgets, state selector and year slider interactivity
- **Integration Lead:** Docker container setup, git repository management, final documentation, deployment and code walkthrough video

## 8. Timeline

| Week | Milestone |
|------|-----------|
| 12 | Design document + data acquisition (this milestone) |
| 13 | Data pipeline, cleaning, merging, tests |
| 14 | Dashboard, Docker, code walkthrough video |
| 15 | Poster session and peer evaluation |

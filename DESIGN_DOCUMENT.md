# Design Document: Housing Market & Affordability Dashboard

## 1. Domain & Motivation

Housing affordability has become one of the most talked about economic issues in the U.S. over the past decade. Home prices have grown much faster than wages, mortgage rates hit historic lows during COVID and then shot up rapidly, and the gap between what homes cost and what families earn has widened in nearly every state. This project integrates data from three separate sources to build an interactive dashboard that lets users explore those trends at both the national and state level across 2010 to 2023.

## 2. Research Questions

1. How has housing affordability changed over time across U.S. states, measured by price-to-income ratio?
2. What is the relationship between national mortgage rates and median home prices over time?
3. Which states are the most and least affordable for homebuyers in any given year?
4. How did major economic events like the 2008 recovery and the COVID-19 era affect housing markets differently across regions?

## 3. Data Sources

| Source | Type | Geographic Level | Frequency | API Key |
|--------|------|-----------------|-----------|---------|
| FRED API | REST API | National | Weekly / Monthly / Quarterly | Yes (free) |
| Census Bureau ACS | REST API | State | Annual (5-year estimates) | Yes (free) |
| Zillow ZHVI | Static CSV | State | Monthly | No |

- FRED key: https://fred.stlouisfed.org/docs/api/api_key.html (rate limit: 120 req/min)
- Census key: https://api.census.gov/data/key_signup.html (rate limit: 500 req/day without key)
- Zillow: https://www.zillow.com/research/data/ — no key, direct CSV download

See `DATA_SOURCES.md` for complete field descriptions and access notes.

## 4. Key Fields

### FRED (national, date-indexed)

| Field | Description | Frequency |
|-------|-------------|-----------|
| `MSPUS` | Median sales price of houses sold (USD) | Quarterly |
| `MORTGAGE30US` | 30-year fixed mortgage rate (%) | Weekly |
| `HOUST` | New housing starts (thousands) | Monthly |
| `CSUSHPINSA` | Case-Shiller home price index | Monthly |
| `RHORUSQ156N` | National homeownership rate (%) | Quarterly |
| `MSACSR` | Monthly supply of houses (months) | Monthly |

### Census ACS 5-Year Estimates (state, annual)

| Field | Description |
|-------|-------------|
| `state_name` | Full state name — join key for Zillow |
| `state_fips` | 2-digit FIPS code |
| `year` | ACS vintage year (2010, 2012, 2014, 2016, 2018, 2020, 2022, 2023) |
| `median_household_income` | Median household income (USD) |
| `median_home_value` | Median owner-occupied home value (USD) |
| `median_gross_rent` | Median gross rent (USD) |
| `homeownership_rate` | Owner-occupied share of occupied units (%) — derived |
| `price_to_income_ratio` | median_home_value / median_household_income — derived |

### Zillow ZHVI (state, monthly)

| Field | Description |
|-------|-------------|
| `RegionName` | State name — join key for Census |
| `date` | Month of observation |
| `zhvi` | Zillow Home Value Index (USD) — smoothed, seasonally adjusted, 35th to 65th percentile |

## 5. Merge Strategy

All three sources run at different frequencies and geographic levels, so we bring them to a common denominator before joining.

**Step 1** — Aggregate Zillow from monthly to annual by taking the mean ZHVI per state per year.

**Step 2** — Aggregate FRED from mixed frequencies to one national average per year for each series.

**Step 3** — Inner join Census to Zillow annual on `state_name == RegionName` and `year`. This keeps only state-year combinations present in both sources.

**Step 4** — Left join FRED annual to the result on `year`. Every state row in a given year gets the same national mortgage rate and price index attached as context columns.

**Final schema** — One row per (state, year). 408 rows, 51 states and territories, years 2010 through 2023.

**Derived columns added after merging:**
- `price_to_income_ratio` = median_home_value / median_household_income

## 6. Architecture

```
Data Acquisition
  fetch_fred.py    → data/fred_housing_data.csv
  fetch_census.py  → data/census_housing_data.csv
  fetch_zillow.py  → data/zillow_zhvi_data.csv

Data Processing
  clean.py   → handles missing values, duplicates, type conversions
  merge.py   → aggregates to annual, joins all three, saves merged.parquet

Dashboard
  dashboard.py (Panel + Plotly)
    - National summary metrics (5 indicator cards)
    - Visualization 1: national home price vs mortgage rate over time
    - Visualization 2: choropleth map + state rankings bar chart
    - Visualization 3: single state affordability drill-down
    - Visualization 4: animated home values across top 15 states

Deployment
  Dockerfile + docker-compose.yml
  Runs at http://localhost:5006/dashboard
```

## 7. Team Roles

- **Data Acquisition (Zaid):** fetch scripts, API integration, error handling, rate limit management
- **Data Engineering:** cleaning pipeline, merge logic, pytest test suite
- **Visualization:** dashboard design, Plotly charts, Panel widgets and interactivity
- **Integration:** Docker setup, git repository management, documentation, code walkthrough video

## 8. Timeline

| Week | Deliverable |
|------|-------------|
| 12 | Design document and working data fetch scripts |
| 13 | Full pipeline with cleaning, merging, and tests |
| 14 | Dashboard, Docker, code walkthrough video |
| 15 | Poster session and peer evaluation |

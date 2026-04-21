# Data Sources

This project pulls from three sources. Two are APIs and one is a static file download. Details on access, fields, and known issues are below.

---

## FRED API

**Base URL:** `https://api.stlouisfed.org/fred/series/observations`  
**API key:** Required (free) — https://fred.stlouisfed.org/docs/api/api_key.html  
**Rate limit:** 120 requests per minute  
**Docs:** https://fred.stlouisfed.org/docs/api/fred/

FRED provides national-level economic time series data. We pull six series, all starting from 2000-01-01.

| Series ID | Description | Frequency |
|-----------|-------------|-----------|
| MSPUS | Median sales price of houses sold | Quarterly |
| MORTGAGE30US | 30-year fixed mortgage average | Weekly |
| HOUST | New privately-owned housing starts | Monthly |
| CSUSHPINSA | S&P/Case-Shiller national home price index | Monthly |
| RHORUSQ156N | U.S. homeownership rate | Quarterly |
| MSACSR | Monthly supply of houses | Monthly |

**Known issues:**
- Missing values are encoded as `"."` — converted to NaN during cleaning
- Series have different frequencies, so the merged table is sparse before annual aggregation

---

## U.S. Census Bureau API (ACS 5-Year Estimates)

**Base URL:** `https://api.census.gov/data/{year}/acs/acs5`  
**API key:** Required (free) — https://api.census.gov/data/key_signup.html  
**Rate limit:** 500 requests/day without a key, higher with one  
**Docs:** https://www.census.gov/data/developers/data-sets.html

We pull state-level housing and income data for 8 years: 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2023. The response is a JSON array where the first element is the header row.

| Variable Code | Column Name | Description |
|---------------|-------------|-------------|
| B19013_001E | median_household_income | Median household income |
| B25077_001E | median_home_value | Median owner-occupied home value |
| B25064_001E | median_gross_rent | Median gross rent |
| B25003_001E | total_occupied_units | Total occupied housing units |
| B25003_002E | owner_occupied_units | Owner-occupied units |
| B25003_003E | renter_occupied_units | Renter-occupied units |
| B01003_001E | total_population | Total population |

Two columns are derived after fetching: `homeownership_rate` and `price_to_income_ratio`.

**Known issues:**
- Values of `-666666666` mean the data was suppressed for privacy — replaced with NaN during cleaning
- ACS 5-year estimates are only released for certain years, which is why the year slider in the dashboard skips odd years

---

## Zillow Home Value Index (ZHVI)

**Download:** https://www.zillow.com/research/data/  
**Selection:** ZHVI → State → All Homes → Smoothed, Seasonally Adjusted  
**API key:** Not required  

ZHVI measures the typical home value at the 35th to 65th percentile for each state on a monthly basis. The raw file is in wide format with one column per month, which we reshape to long format before merging.

| Field | Description |
|-------|-------------|
| RegionName | State name — used as the join key |
| SizeRank | Population-based size ranking |
| Date columns | Monthly ZHVI value in USD (e.g. `2020-01-31`) |

**Known issues:**
- Zillow changes the download URL periodically — the fetch script tries two URLs before falling back to a synthetic dataset
- `StateName` column is empty in the raw file, so we join on `RegionName` directly

# Data Sources — API Keys, Rate Limits & Access Notes

## Source 1: FRED API (Federal Reserve Economic Data)
- **Type:** REST API (JSON responses)
- **Base URL:** `https://api.stlouisfed.org/fred/series/observations`
- **API Key:** Required (free). Register at https://fred.stlouisfed.org/docs/api/api_key.html
- **Rate Limits:** 120 requests per minute
- **Authentication:** API key passed as query parameter
- **Documentation:** https://fred.stlouisfed.org/docs/api/fred/
- **Series Used:**
  | Series ID | Description | Frequency |
  |-----------|-------------|-----------|
  | MSPUS | Median Sales Price of Houses Sold | Quarterly |
  | MORTGAGE30US | 30-Year Fixed Rate Mortgage Average | Weekly |
  | HOUST | Housing Starts: Total New Privately Owned | Monthly |
  | CSUSHPINSA | S&P/Case-Shiller National Home Price Index | Monthly |
  | RHORUSQ156N | Homeownership Rate for the United States | Quarterly |
  | MSACSR | Monthly Supply of Houses | Monthly |
- **Key Fields:** `date`, `value` (numeric observation)
- **Notes:** Missing values encoded as `"."`. Different series have different frequencies, requiring careful alignment when merging.

---

## Source 2: U.S. Census Bureau API (American Community Survey)
- **Type:** REST API (JSON array responses)
- **Base URL:** `https://api.census.gov/data/{year}/acs/acs5`
- **API Key:** Required (free). Register at https://api.census.gov/data/key_signup.html
- **Rate Limits:** 500 requests/day without key; higher with key
- **Authentication:** API key passed as query parameter
- **Documentation:** https://www.census.gov/data/developers/data-sets.html
- **Variables Used:**
  | Variable | Description |
  |----------|-------------|
  | B19013_001E | Median household income (past 12 months) |
  | B25077_001E | Median value of owner-occupied housing units |
  | B25064_001E | Median gross rent |
  | B25003_001E | Total occupied housing units |
  | B25003_002E | Owner-occupied housing units |
  | B25003_003E | Renter-occupied housing units |
  | B01003_001E | Total population |
- **Geographic Level:** State (FIPS codes)
- **Years Available:** ACS 5-year estimates from 2009 onward. We use: 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2023
- **Key Fields:** `NAME` (state name), `state` (FIPS code), variable values
- **Notes:** Values of `-666666666` indicate suppressed data. Response format is a JSON array where the first element is headers.

---

## Source 3: Zillow Home Value Index (Static CSV)
- **Type:** Static CSV download (no API key required)
- **Download URL:** https://www.zillow.com/research/data/
  - Select: ZHVI → State → All Homes → Smoothed, Seasonally Adjusted
- **Rate Limits:** None (direct file download)
- **Authentication:** None
- **Documentation:** https://www.zillow.com/research/data/
- **Key Fields:**
  | Field | Description |
  |-------|-------------|
  | RegionID | Zillow's unique region identifier |
  | RegionName | State name |
  | SizeRank | Population-based ranking |
  | Date columns | Monthly ZHVI values (YYYY-MM-DD format) |
- **Notes:** Data comes in wide format (one column per month). We reshape to long format for merging. Zillow frequently changes download URLs — we include fallback logic. ZHVI represents the "typical" home value (35th-65th percentile).

---

## Merge Strategy

**Join keys:**
- FRED ↔ Census: Merge on **time period** (year/quarter). FRED data is national-level; Census is state-level. We'll aggregate or use national-level FRED data as context alongside state-level Census data.
- Census ↔ Zillow: Merge on **state name** + **year/month**. Both have state-level geography.
- All three: Final merged dataset keyed on **(state, date)** with national economic indicators from FRED applied across all states for a given time period.

**Challenges:**
- Different frequencies (weekly, monthly, quarterly, annual) — will resample to monthly or quarterly
- FRED is national only; Census and Zillow are state-level
- Missing data across sources needs careful handling

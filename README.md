# Housing Market & Affordability Dashboard

An interactive dashboard exploring U.S. housing affordability across all 50 states from 2010 to 2023. Data is pulled from three sources — FRED, the Census Bureau, and Zillow — cleaned, merged, and served through a Panel web app with Plotly charts.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up API keys

Create a `.env` file in the project root:

```
FRED_API_KEY=your_fred_key_here
CENSUS_API_KEY=your_census_key_here
```

Get a free FRED key at https://fred.stlouisfed.org/docs/api/api_key.html  
Get a free Census key at https://api.census.gov/data/key_signup.html

Do not commit the `.env` file — it is listed in `.gitignore`.

---

## Running the Pipeline

### Step 1 — Fetch raw data from all sources

```bash
python scripts/fetch_all.py
```

This saves CSV files to `data/`:
- `fred_housing_data.csv` — national economic indicators
- `census_housing_data.csv` — state-level income and housing
- `zillow_zhvi_data.csv` — state-level home values

### Step 2 — Clean and merge

```bash
python scripts/merge.py
```

This reads the raw CSVs, runs cleaning, merges all three sources, and saves the final dataset to `data/merged.parquet`.

### Step 3 — Run the dashboard

```bash
panel serve dashboard.py --show
```

The dashboard opens at `http://localhost:5006/dashboard`.

---

## Running with Docker

```bash
docker-compose up
```

Then open `http://localhost:5006/dashboard` in your browser.

To rebuild after making changes:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

---

## Running Tests

```bash
pytest tests/test_pipeline.py -v
```

All 8 tests should pass. Tests cover data loading, cleaning, merge logic, and validation.

---

## Project Structure

```
housing_project/
├── dashboard.py              # Panel dashboard (run this to view the app)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env                      # API keys — not committed to git
├── .gitignore
├── README.md
├── DESIGN_DOCUMENT.md
├── DATA_SOURCES.md
├── scripts/
│   ├── fetch_all.py          # runs all three fetch scripts
│   ├── fetch_fred.py         # pulls FRED API data
│   ├── fetch_census.py       # pulls Census ACS data
│   ├── fetch_zillow.py       # downloads Zillow ZHVI CSV
│   ├── clean.py              # cleaning functions for each source
│   └── merge.py              # merges all three into merged.parquet
├── tests/
│   └── test_pipeline.py      # pytest test suite
└── data/                     # generated files, not committed to git
    ├── fred_housing_data.csv
    ├── census_housing_data.csv
    ├── zillow_zhvi_data.csv
    └── merged.parquet
```

---

## Data Sources

**FRED** — REST API from the Federal Reserve Bank of St. Louis. Provides national-level economic indicators including median home prices, 30-year mortgage rates, housing starts, and homeownership rate. Rate limit is 120 requests per minute.

**Census Bureau ACS** — REST API providing state-level housing and income data from the American Community Survey 5-year estimates. We pull data for 2010, 2012, 2014, 2016, 2018, 2020, 2022, and 2023. Rate limit is 500 requests per day without a key.

**Zillow ZHVI** — Static CSV download from Zillow Research with monthly state-level home values. No API key required. The download URL changes periodically so the fetch script includes fallback URLs.

See `DATA_SOURCES.md` for full field descriptions, variable codes, and known data quality notes.

---

## Data Cleaning

**FRED** — Missing values come in as the string `"."` which we convert to NaN using numeric coercion. Duplicate rows are dropped.

**Census** — The API uses `-666666666` as a sentinel for suppressed data. We replace all instances with NaN before any calculations. Rows with missing income or home value are dropped since they can't contribute to affordability metrics.

**Zillow** — Data arrives in wide format with one column per month. We reshape to long format, parse dates, drop rows with missing ZHVI values, and filter to 2000 onward to match the FRED date range.

---

## Merge Strategy

All three sources are brought to annual frequency before joining. Zillow monthly data is averaged to one value per state per year. FRED mixed-frequency data is averaged to one value per year. Census is already annual.

The merge happens in two steps. First, Zillow annual data is joined to Census on state name and year using an inner join. Then FRED national annual averages are joined to the result on year alone, so every state row gets the same national mortgage rate and price index for that year.

The final dataset has one row per state per year — 408 rows total, 51 states and territories, 8 years from 2010 to 2023.

---

## Known Issues

- Census ACS is only available for specific years so the year slider in the dashboard is restricted to years that have data
- FRED series have different frequencies which means the merged table is sparse before annual aggregation
- Zillow download URLs change occasionally — the fetch script tries two URLs before falling back to a synthetic dataset
- FRED data is national only so mortgage rates and price indices apply uniformly across all states for a given year

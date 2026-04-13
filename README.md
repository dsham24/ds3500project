# Housing Market & Affordability Dashboard

An interactive dashboard exploring U.S. housing affordability by integrating data from FRED, the Census Bureau, and Zillow.

---

## Quick Start

### 1. Install dependencies
pip install requests pandas pytest

---

### 2. Set up API keys (optional)

The scripts currently include API keys for development. For production use:

export FRED_API_KEY="your_key_here"
export CENSUS_API_KEY="your_key_here"

---

### 3. Fetch all data
python scripts/fetch_all.py

This creates CSV files in the `data/` directory:
- fred_housing_data.csv — National economic indicators (FRED)
- census_housing_data.csv — State-level housing & income (Census)
- zillow_zhvi_data.csv — State-level home values (Zillow)

---

### 4. Run full pipeline
python scripts/merge.py

---

### 5. Run tests
cd housing_project
pytest tests/test_pipeline.py -v

---

## Data Pipeline

This project builds a data pipeline that:

- Fetches data from multiple APIs and sources  
- Cleans each dataset (missing values, duplicates, types)  
- Merges datasets using appropriate join strategies  
- Validates data quality using pytest  
- Saves a final cleaned dataset  

---

## Data Cleaning Decisions

- Census Data:
  - Replaced suppressed values (-666666666) with NaN
  - Removed rows missing key variables (income or home value)

- FRED Data:
  - Converted all values to numeric
  - Handled missing values ("." → NaN)

- Zillow Data:
  - Removed rows with missing home values (zhvi)
  - Converted dates to datetime format

- All datasets:
  - Removed duplicate rows
  - Standardized column types

---

## Known Data Issues

- FRED data contains mixed frequencies (weekly, monthly, quarterly)
- Census data is only available every few years (ACS 5-year estimates)
- Zillow data is monthly and aggregated to yearly averages
- FRED data is national-level, while Census and Zillow are state-level  
  → handled by merging on year and applying national indicators across states

---

## Data Merge Strategy

1. Zillow data aggregated to yearly state-level values  
2. Census merged with Zillow using:
   - RegionName = state_name
   - year
3. FRED data aggregated to yearly national averages  
4. Final merge performed on year  

Final dataset includes:
- State-level housing and income data  
- National economic indicators  
- Derived metrics (price-to-income ratio)

---

## Output

The final cleaned dataset is saved as:

data/merged.parquet

---

## Testing

Pytest is used to check that the pipeline works correctly.

The tests check:
- Data cleaning (duplicates removed, valid values)
- Merge logic (correct columns, non-empty dataset)
- Data quality (no negative values, valid ratios)

Some data required cleaning due to missing values and inconsistencies across sources.

Run:
pytest

---

## Project Structure

housing_project/
├── README.md
├── DESIGN_DOCUMENT.md
├── DATA_SOURCES.md
├── scripts/
│   ├── fetch_all.py
│   ├── fetch_fred.py
│   ├── fetch_census.py
│   ├── fetch_zillow.py
│   ├── clean.py
│   ├── merge.py
├── tests/
│   ├── test_pipeline.py
└── data/
    ├── fred_housing_data.csv
    ├── census_housing_data.csv
    ├── zillow_zhvi_data.csv
    └── merged.parquet

---

## Data Sources

See DATA_SOURCES.md for:
- API documentation  
- Rate limits  
- Field descriptions  
- Data quality notes

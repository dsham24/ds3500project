"""
Fetch housing and income data from the U.S. Census Bureau API

Uses the American Community Survey 5-Year Estimates
Data fetched by state:
- B19013_001E: Median household income
- B25077_001E: Median home value
- B25064_001E: Median gross rent
- B25003_001E: Total housing units (occupied)
- B25003_002E: Owner-occupied housing units
- B25003_003E: Renter-occupied housing units
- B01003_001E: Total population

API Documentation: https://www.census.gov/data/developers/data-sets.html
Rate Limits: 500 requests per day without key; higher with key
API Key: Free, register at https://api.census.gov/data/key_signup.html
"""

import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY")
BASE_URL = "https://api.census.gov/data/{year}/acs/acs5"

# variables to fetch
VARIABLES = {
    "B19013_001E": "median_household_income",
    "B25077_001E": "median_home_value",
    "B25064_001E": "median_gross_rent",
    "B25003_001E": "total_occupied_units",
    "B25003_002E": "owner_occupied_units",
    "B25003_003E": "renter_occupied_units",
    "B01003_001E": "total_population",
}

# ACS 5-year data available from 2009 onward
YEARS = [2010, 2012, 2014, 2016, 2018, 2020, 2022, 2023]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def fetch_census_state_data(year, api_key=CENSUS_API_KEY):
    """
    Fetch ACS 5-year housing/income variables for all US states.

    Parameters
    ----------
    year : int
        The ACS vintage year (e.g., 2023 for 2019-2023 estimates).
    api_key : str
        Your Census API key.

    Returns
    -------
    pd.DataFrame
        DataFrame with one row per state, columns for each variable.
    """
    var_list = ",".join(["NAME"] + list(VARIABLES.keys()))
    url = BASE_URL.format(year=year)

    params = {
        "get": var_list,
        "for": "state:*",
        "key": api_key,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    # first row is headers, rest is data
    headers = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=headers)

    # rename variables to human-readable names
    df = df.rename(columns=VARIABLES)
    df = df.rename(columns={"NAME": "state_name", "state": "state_fips"})

    # convert numeric columns
    for col in VARIABLES.values():
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # add year column
    df["year"] = year

    return df


def fetch_all_census_data(years=YEARS, api_key=CENSUS_API_KEY):
    """
    Fetch ACS data for all specified years and combine.

    Parameters
    years : list of int
        ACS vintage years to fetch.
    api_key : str
        Your Census API key.

    Returns
    pd.DataFrame
        Combined DataFrame with data for all years and states.
    """
    all_data = []

    for year in years:
        print(f"Fetching ACS 5-Year data for {year}...")
        try:
            df = fetch_census_state_data(year, api_key)
            all_data.append(df)
            print(f"  Got {len(df)} states/territories")
        except Exception as e:
            print(f"  ERROR for {year}: {e}")

    if not all_data:
        return pd.DataFrame()

    combined = pd.concat(all_data, ignore_index=True)

    # calculate derived columns
    combined["homeownership_rate"] = (
        combined["owner_occupied_units"] / combined["total_occupied_units"] * 100
    ).round(1)
    combined["price_to_income_ratio"] = (
        combined["median_home_value"] / combined["median_household_income"]
    ).round(2)

    return combined


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("Fetching Census Bureau Housing & Income Data")
    print("=" * 60)

    df = fetch_all_census_data()

    # save full dataset
    output_path = os.path.join(OUTPUT_DIR, "census_housing_data.csv")
    df.to_csv(output_path, index=False)
    print(f"\nSaved full dataset: {output_path} ({len(df)} rows)")

    # save sample (first 100 rows)
    sample_path = os.path.join(OUTPUT_DIR, "census_housing_sample.csv")
    df.head(100).to_csv(sample_path, index=False)
    print(f"Saved sample: {sample_path} (100 rows)")

    # print summary
    print(f"\nYears covered: {sorted(df['year'].unique())}")
    print(f"States/territories: {df['state_name'].nunique()}")
    print(f"\nSample data (2023, first 5 states):")
    sample = df[df["year"] == df["year"].max()].head()
    print(sample[["state_name", "median_household_income", "median_home_value",
                   "price_to_income_ratio"]].to_string(index=False))

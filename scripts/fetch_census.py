import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY")
BASE_URL = "https://api.census.gov/data/{year}/acs/acs5"

# ACS variable codes and their readable names
VARIABLES = {
    "B19013_001E": "median_household_income",
    "B25077_001E": "median_home_value",
    "B25064_001E": "median_gross_rent",
    "B25003_001E": "total_occupied_units",
    "B25003_002E": "owner_occupied_units",
    "B25003_003E": "renter_occupied_units",
    "B01003_001E": "total_population",
}

# ACS 5-year estimates are available every 1-2 years starting from 2009
YEARS = [2010, 2012, 2014, 2016, 2018, 2020, 2022, 2023]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def fetch_census_state_data(year, api_key=CENSUS_API_KEY):
    """
    Fetch ACS 5-year estimates for all states for a given year.

    Parameters
    year : int
    api_key : str

    Returns
    pd.DataFrame with one row per state
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
    # first row is column headers
    headers = data[0]
    rows = data[1:]

    df = pd.DataFrame(rows, columns=headers)

    # rename to readable column names
    df = df.rename(columns=VARIABLES)
    df = df.rename(columns={"NAME": "state_name", "state": "state_fips"})

    for col in VARIABLES.values():
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["year"] = year
    return df


def fetch_all_census_data(years=YEARS, api_key=CENSUS_API_KEY):
    """
    Fetch ACS data for all years and combine into one DataFrame.

    Parameters
    years : list of int
    api_key : str

    Returns
    pd.DataFrame
    """
    all_data = []

    for year in years:
        print(f"  Fetching {year}...")
        try:
            df = fetch_census_state_data(year, api_key)
            all_data.append(df)
            print(f"    {len(df)} states")
        except Exception as e:
            print(f"    Failed for {year}: {e}")

    if not all_data:
        return pd.DataFrame()

    combined = pd.concat(all_data, ignore_index=True)

    # derived columns
    combined["homeownership_rate"] = (
        combined["owner_occupied_units"] / combined["total_occupied_units"] * 100
    ).round(1)
    combined["price_to_income_ratio"] = (
        combined["median_home_value"] / combined["median_household_income"]
    ).round(2)

    return combined


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Fetching Census ACS housing data...")

    df = fetch_all_census_data()

    output_path = os.path.join(OUTPUT_DIR, "census_housing_data.csv")
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} rows to {output_path}")

    sample_path = os.path.join(OUTPUT_DIR, "census_housing_sample.csv")
    df.head(100).to_csv(sample_path, index=False)

    print(f"Years: {sorted(df['year'].unique())}")
    print(f"States: {df['state_name'].nunique()}")

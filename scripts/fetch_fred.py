import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv

load_dotenv()
FRED_API_KEY = os.environ.get("FRED_API_KEY")
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# FRED series to pull
SERIES = {
    "MSPUS": "Median Sales Price of Houses Sold (USD)",
    "MORTGAGE30US": "30-Year Fixed Rate Mortgage Average (%)",
    "HOUST": "Housing Starts (Thousands of Units)",
    "CSUSHPINSA": "S&P/Case-Shiller National Home Price Index",
    "RHORUSQ156N": "Homeownership Rate (%)",
    "MSACSR": "Monthly Supply of Houses (Months)",
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def fetch_fred_series(series_id, api_key, start_date="2000-01-01"):
    """
    Fetch a single FRED series by ID.

    Parameters
    series_id : str
    api_key : str
    start_date : str

    Returns
    pd.DataFrame with columns [date, series_id]
    """
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()

    data = response.json()
    observations = data.get("observations", [])

    df = pd.DataFrame(observations)
    if df.empty:
        print(f"  No data returned for {series_id}")
        return pd.DataFrame(columns=["date", series_id])

    df = df[["date", "value"]].copy()
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])

    # FRED uses "." for missing values
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")

    return df


def fetch_all_fred_data(api_key=FRED_API_KEY, start_date="2000-01-01"):
    """
    Fetch all FRED series and merge into a single wide DataFrame.

    Parameters
    api_key : str
    start_date : str

    Returns
    pd.DataFrame
    """
    all_data = []

    for series_id, description in SERIES.items():
        print(f"  {series_id}: {description}")
        df = fetch_fred_series(series_id, api_key, start_date)
        all_data.append(df)
        time.sleep(0.5)

    # outer join all series on date
    merged = all_data[0]
    for df in all_data[1:]:
        merged = pd.merge(merged, df, on="date", how="outer")

    merged = merged.sort_values("date").reset_index(drop=True)
    return merged


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Fetching FRED housing data...")

    df = fetch_all_fred_data()

    output_path = os.path.join(OUTPUT_DIR, "fred_housing_data.csv")
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} rows to {output_path}")

    sample_path = os.path.join(OUTPUT_DIR, "fred_housing_sample.csv")
    df.head(100).to_csv(sample_path, index=False)

    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

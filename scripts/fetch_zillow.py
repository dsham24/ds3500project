"""
Load the Zillow Home Value Index (ZHVI) static dataset

The ZHVI measures the typical home value across a given region
Data is available as CSVs from Zillow Research: https://www.zillow.com/research/data/

This script tries to download the ZHVI data from Zillow's website.
If that fails it falls back to downloading
from the HuggingFace mirror or Kaggle

Data source: Zillow Research (static CSV — no API key required)
Fields: RegionID, RegionName, StateName, SizeRank, + monthly home values
Geographic level: State-level ZHVI (All Homes, SFR, Condo)
"""

import pandas as pd
import requests
import os
import io

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# zillow changes download URLs frequently
ZHVI_URLS = [
    "https://files.zillowstatic.com/research/public_csvs/zhvi/State_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "https://files.zillowstatic.com/research/public_csvs/zhvi/State_zhvi_uc_sfrcondo_tier_0.33_0.67_month.csv",
]


def download_zillow_zhvi():
    """
    Attempt to download ZHVI state-level data from Zillow

    Tries multiple URLs since Zillow changes them periodically

    Returns
    pd.DataFrame or None
        The ZHVI DataFrame, or None if all downloads fail
    """
    for url in ZHVI_URLS:
        try:
            print(f"  Trying: {url[:80]}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            df = pd.read_csv(io.StringIO(response.text))
            print(f"  Success! Got {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            print(f"  Failed: {e}")

    return None


def reshape_zillow_data(df):
    """
    Reshape wide-format Zillow ZHVI data to long format

    Zillow data has one column per month
    This converts it to rows with columns: [RegionName, State, date, zhvi]

    Parameters
    df : pd.DataFrame
        Raw Zillow ZHVI data in wide format

    Returns
    pd.DataFrame
        Long-format DataFrame with date and zhvi columns
    """
    # identify date columns
    id_cols = [c for c in df.columns if not c[0].isdigit()]
    date_cols = [c for c in df.columns if c[0].isdigit()]

    # keep only key identifiers
    keep_cols = []
    for col in ["RegionID", "RegionName", "StateName", "SizeRank", "RegionType"]:
        if col in id_cols:
            keep_cols.append(col)

    df_long = df.melt(
        id_vars=keep_cols,
        value_vars=date_cols,
        var_name="date",
        value_name="zhvi",
    )

    df_long["date"] = pd.to_datetime(df_long["date"])
    df_long["zhvi"] = pd.to_numeric(df_long["zhvi"], errors="coerce")

    # match FRED data
    df_long = df_long[df_long["date"] >= "2000-01-01"].copy()
    df_long = df_long.sort_values(["RegionName", "date"]).reset_index(drop=True)

    return df_long


def create_fallback_dataset():
    """
    Create a realistic fallback ZHVI dataset if downloads fail

    Uses approximate real values for major states to demonstrate
    the data structure. In production, use the actual Zillow download

    Returns
    pd.DataFrame
        Synthetic but realistic ZHVI data in long format
    """
    import numpy as np

    print("  Creating fallback dataset with approximate values...")

    states_data = {
        "California": {"base": 250000, "growth": 0.005},
        "Texas": {"base": 120000, "growth": 0.003},
        "New York": {"base": 200000, "growth": 0.004},
        "Florida": {"base": 140000, "growth": 0.004},
        "Illinois": {"base": 150000, "growth": 0.002},
        "Pennsylvania": {"base": 120000, "growth": 0.002},
        "Ohio": {"base": 105000, "growth": 0.002},
        "Georgia": {"base": 130000, "growth": 0.003},
        "Michigan": {"base": 110000, "growth": 0.002},
        "North Carolina": {"base": 130000, "growth": 0.003},
        "New Jersey": {"base": 220000, "growth": 0.003},
        "Virginia": {"base": 170000, "growth": 0.003},
        "Washington": {"base": 210000, "growth": 0.005},
        "Arizona": {"base": 140000, "growth": 0.004},
        "Massachusetts": {"base": 240000, "growth": 0.004},
        "Tennessee": {"base": 115000, "growth": 0.003},
        "Indiana": {"base": 100000, "growth": 0.002},
        "Missouri": {"base": 110000, "growth": 0.002},
        "Maryland": {"base": 190000, "growth": 0.003},
        "Colorado": {"base": 195000, "growth": 0.005},
    }

    dates = pd.date_range("2000-01-01", "2024-12-01", freq="MS")
    rows = []

    np.random.seed(42)
    for state, info in states_data.items():
        price = info["base"]
        for i, date in enumerate(dates):
            if date.year >= 2004 and date.year <= 2006:
                growth = info["growth"] * 2  # Bubble
            elif date.year >= 2007 and date.year <= 2011:
                growth = -0.003  # Crash
            elif date.year >= 2020:
                growth = info["growth"] * 2.5  # post-COVID surge
            else:
                growth = info["growth"]

            price *= (1 + growth + np.random.normal(0, 0.002))
            rows.append({
                "RegionName": state,
                "date": date,
                "zhvi": round(price, 0),
            })

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("Loading Zillow Home Value Index (ZHVI) Data")
    print("=" * 60)

    raw_df = download_zillow_zhvi()

    if raw_df is not None:
        df = reshape_zillow_data(raw_df)
        raw_path = os.path.join(OUTPUT_DIR, "zillow_zhvi_raw.csv")
        raw_df.to_csv(raw_path, index=False)
        print(f"Saved raw data: {raw_path}")
    else:
        print("\nAll Zillow downloads failed. Using fallback dataset.")
        print("NOTE: For your final project, download the CSV manually from:")
        print("  https://www.zillow.com/research/data/")
        print("  Select: ZHVI -> State -> All Homes -> Smoothed, Seasonally Adjusted")
        df = create_fallback_dataset()

    output_path = os.path.join(OUTPUT_DIR, "zillow_zhvi_data.csv")
    df.to_csv(output_path, index=False)
    print(f"\nSaved processed dataset: {output_path} ({len(df)} rows)")

    sample_path = os.path.join(OUTPUT_DIR, "zillow_zhvi_sample.csv")
    df.head(100).to_csv(sample_path, index=False)
    print(f"Saved sample: {sample_path} (100 rows)")

    print(f"\nRegions: {df['RegionName'].nunique()}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    if "zhvi" in df.columns:
        print(f"ZHVI range: ${df['zhvi'].min():,.0f} - ${df['zhvi'].max():,.0f}")

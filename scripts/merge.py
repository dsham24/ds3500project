import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def merge_all(fred, census, zillow):
    """
    Merge FRED, Census, and Zillow into one dataset.

    Zillow and FRED are aggregated to annual averages first.
    Census and Zillow are joined on state name and year.
    FRED national data is joined on year only.
    """
    fred["year"] = fred["date"].dt.year
    zillow["year"] = zillow["date"].dt.year

    # annual average for each FRED series
    fred_yearly = fred.groupby("year").mean(numeric_only=True).reset_index()

    # annual average ZHVI per state
    zillow_yearly = (
        zillow.groupby(["RegionName", "year"])["zhvi"]
        .mean()
        .reset_index()
    )

    # join Census to Zillow on state name and year
    merged = pd.merge(
        zillow_yearly,
        census,
        left_on=["RegionName", "year"],
        right_on=["state_name", "year"],
        how="inner"
    )

    # attach national FRED data by year
    merged = pd.merge(
        merged,
        fred_yearly,
        on="year",
        how="left"
    )

    merged["price_to_income_ratio"] = (
        merged["median_home_value"] / merged["median_household_income"]
    )

    return merged


if __name__ == "__main__":
    fred = pd.read_csv(os.path.join(DATA_DIR, "fred_housing_data.csv"))
    census = pd.read_csv(os.path.join(DATA_DIR, "census_housing_data.csv"))
    zillow = pd.read_csv(os.path.join(DATA_DIR, "zillow_zhvi_data.csv"))

    from clean import clean_fred, clean_census, clean_zillow

    fred = clean_fred(fred)
    census = clean_census(census)
    zillow = clean_zillow(zillow)

    merged = merge_all(fred, census, zillow)

    output_path = os.path.join(DATA_DIR, "merged.parquet")
    merged.to_parquet(output_path, index=False)

    # save CSV as a readable backup
    merged.to_csv(os.path.join(DATA_DIR, "merged.csv"), index=False)

    print(f"Saved merged dataset to {output_path}")

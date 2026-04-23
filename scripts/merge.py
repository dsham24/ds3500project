import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def merge_all(fred, census, zillow):
    """
    Merge FRED, Census, and Zillow into a single state-year dataset.

    All three sources run at different frequencies and geographic levels,
    so we bring them to a common denominator before joining:
    - Zillow is monthly, aggregated to annual averages per state
    - FRED is weekly/monthly/quarterly, aggregated to annual national averages
    - Census is already annual at the state level

    Join logic:
    - Census joins to Zillow on state_name and year (inner join keeps only
      states present in both, which in practice is all 50 states)
    - FRED national averages join on year only, adding macro context to
      every state row for that year

    Parameters:
    
    fred : pd.DataFrame
        - Cleaned FRED data with a parsed date column.
    census : pd.DataFrame
        - Cleaned Census ACS data with state_name and year columns.
    zillow : pd.DataFrame
        - Cleaned Zillow data with RegionName and date columns.

    Returns:
    
    pd.DataFrame
        Merged dataset with one row per (state, year).
    """
    # extract year from dates so we can group by year across all three sources
    fred["year"] = fred["date"].dt.year
    zillow["year"] = zillow["date"].dt.year

    # aggregate FRED to annual averages: mixed frequencies collapse to one value per year
    fred_yearly = fred.groupby("year").mean(numeric_only=True).reset_index()

    # aggregate Zillow to annual averages per state: monthly ZHVI collapses to one value per state per year
    zillow_yearly = (
        zillow.groupby(["RegionName", "year"])["zhvi"]
        .mean()
        .reset_index()
    )

    # inner join Census to Zillow on state name and year: keeps states present in both sources
    merged = pd.merge(
        zillow_yearly,
        census,
        left_on=["RegionName", "year"],
        right_on=["state_name", "year"],
        how="inner"
    )

    # left join FRED national averages by year: every state row gets the same national mortgage rate and price index
    merged = pd.merge(
        merged,
        fred_yearly,
        on="year",
        how="left"
    )

    # derive price-to-income ratio: measures how many years of income it takes to buy the median home
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

    # save as parquet for efficient loading in the dashboard
    output_path = os.path.join(DATA_DIR, "merged.parquet")
    merged.to_parquet(output_path, index=False)

    # save CSV for analysis
    merged.to_csv(os.path.join(DATA_DIR, "merged.csv"), index=False)

    print(f"Saved merged dataset to {output_path}")

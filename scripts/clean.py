import pandas as pd


def clean_fred(df):
    """
    Clean raw FRED housing data.

    Handles date parsing, numeric conversion, and deduplication.
    FRED encodes missing observations as "." which pandas reads as a string,
    so we use errors="coerce" to convert those to NaN.

    Parameters:

    df : pd.DataFrame
        Raw FRED data loaded from fred_housing_data.csv.

    Returns:
    
    pd.DataFrame
        Cleaned FRED data sorted by date.
    """
    df = df.copy()

    # parse date so we can sort and group by time period later
    df["date"] = pd.to_datetime(df["date"])

    # coerce to numeric: FRED uses "." for missing values which would otherwise stay as strings
    for col in df.columns:
        if col != "date":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # drop exact duplicate rows that can appear when series overlap on the same date
    df = df.drop_duplicates()

    df = df.sort_values("date").reset_index(drop=True)
    return df


def clean_census(df):
    """
    Clean raw Census ACS housing and income data.

    The Census API uses -666666666 as a sentinel for suppressed data,
    meaning the value exists but was withheld for privacy. We replace
    these with NaN so they don't corrupt derived metrics like
    price_to_income_ratio. Rows missing income or home value are dropped
    because they can't contribute to any affordability calculation.

    Parameters:

    df : pd.DataFrame
        Raw Census data loaded from census_housing_data.csv.

    Returns:

    pd.DataFrame
        Cleaned Census data with suppressed values removed.
    """
    df = df.copy()

    # replace Census suppressed data sentinel with NaN so it doesn't corrupt calculations
    df.replace(-666666666, pd.NA, inplace=True)

    # drop duplicates that can occur if the same state/year gets fetched twice
    df = df.drop_duplicates()

    # drop rows missing income or home value since these are required for affordability metrics
    df = df.dropna(subset=["median_household_income", "median_home_value"])

    return df


def clean_zillow(df):
    """
    Clean raw Zillow ZHVI state-level data.

    Zillow data arrives in long format after reshaping in fetch_zillow.py.
    We parse dates, drop rows with no home value, and remove duplicates.
    Rows with null zhvi are useless for any visualization or merge.

    Parameters:
    
    df : pd.DataFrame
        Raw Zillow data loaded from zillow_zhvi_data.csv.

    Returns:
    
    pd.DataFrame
        Cleaned Zillow data with valid home values and parsed dates.
    """
    df = df.copy()

    # parse date so we can extract year for the annual aggregation in merge.py
    df["date"] = pd.to_datetime(df["date"])

    # drop rows with no home value since they can't be aggregated or visualized
    df = df.dropna(subset=["zhvi"])

    # drop duplicates that can appear if the same state/month appears twice in the raw file
    df = df.drop_duplicates()

    return df

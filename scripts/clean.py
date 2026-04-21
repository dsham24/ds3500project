import pandas as pd


def clean_fred(df):
    """Clean FRED data: parse dates, convert to numeric, drop duplicates."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    for col in df.columns:
        if col != "date":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.drop_duplicates()
    return df


def clean_census(df):
    """Clean Census data: replace suppressed values, drop duplicates and nulls."""
    df = df.copy()
    # Census uses -666666666 for suppressed/privacy restricted data points
    df.replace(-666666666, pd.NA, inplace=True)
    df = df.drop_duplicates()
    df = df.dropna(subset=["median_household_income", "median_home_value"])
    return df


def clean_zillow(df):
    """Clean Zillow data: parse dates, drop missing home values and duplicates."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["zhvi"])
    df = df.drop_duplicates()
    return df

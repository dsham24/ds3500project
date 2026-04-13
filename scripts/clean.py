import pandas as pd

def clean_fred(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    for col in df.columns:
        if col != "date":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.drop_duplicates()
    return df

def clean_census(df):
    df = df.copy()
    df.replace(-666666666, pd.NA, inplace=True)
    df = df.drop_duplicates()
    df = df.dropna(subset=["median_household_income", "median_home_value"])
    return df

def clean_zillow(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["zhvi"])
    df = df.drop_duplicates()
    return df

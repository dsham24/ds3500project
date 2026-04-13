import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from clean import clean_census
from merge import merge_all

def sample_data():
    fred = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=3),
        "value": [1, 2, 3]
    })

    census = pd.DataFrame({
        "state_name": ["Texas", "Texas", "California"],
        "year": [2020, 2021, 2020],
        "median_household_income": [50000, 52000, 60000],
        "median_home_value": [200000, 210000, 300000]
    })

    zillow = pd.DataFrame({
        "RegionName": ["Texas", "California"],
        "date": pd.to_datetime(["2020-01-01", "2020-01-01"]),
        "zhvi": [210000, 310000]
    })

    return fred, census, zillow

def test_no_negative_income():
    df = pd.DataFrame({
        "median_household_income": [50000, 60000],
        "median_home_value": [200000, 300000]
    })
    df = clean_census(df)
    assert (df["median_household_income"] >= 0).all()

def test_no_duplicates():
    df = pd.DataFrame({
        "median_household_income": [50000, 50000],
        "median_home_value": [200000, 200000]
    })
    df = clean_census(df)
    assert df.duplicated().sum() == 0

def test_merge_not_empty():
    fred, census, zillow = sample_data()
    merged = merge_all(fred, census, zillow)
    assert len(merged) > 0

def test_merge_has_ratio():
    fred, census, zillow = sample_data()
    merged = merge_all(fred, census, zillow)
    assert "price_to_income_ratio" in merged.columns

def test_year_column_exists():
    fred, census, zillow = sample_data()
    merged = merge_all(fred, census, zillow)
    assert "year" in merged.columns

def test_valid_ratio():
    fred, census, zillow = sample_data()
    merged = merge_all(fred, census, zillow)
    assert (merged["price_to_income_ratio"] > 0).all()

def test_zhvi_not_negative():
    fred, census, zillow = sample_data()
    merged = merge_all(fred, census, zillow)
    assert (merged["zhvi"] >= 0).all()

def test_state_names_exist():
    fred, census, zillow = sample_data()
    merged = merge_all(fred, census, zillow)
    assert merged["RegionName"].notna().all()

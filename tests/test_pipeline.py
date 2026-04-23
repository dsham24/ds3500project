"""
test_pipeline.py - pytest test suite for the Housing Market pipeline

Tests are organized into four categories:
- Data loading
- Data cleaning (one test per source)
- Merge logic
- Data validation

Fixtures provide realistic sample data that mirrors the actual
data structure including known edge cases like Census sentinel values.

Run with:
    pytest tests/test_pipeline.py -v
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from clean import clean_fred, clean_census, clean_zillow
from merge import merge_all


# Fixtures: realistic sample data mirroring actual data structure

@pytest.fixture
def fred_raw():
    """
    Sample FRED data mimicking the real wide-format output.
    Includes missing values encoded as NaN (FRED uses '.' which
    fetch_fred converts to NaN via pd.to_numeric).
    Includes a duplicate row to test deduplication.
    """
    return pd.DataFrame({
        "date": [
            "2020-01-01", "2020-01-01",  # dupe
            "2020-04-01", "2020-07-01",
            "2021-01-01", "2021-04-01",
        ],
        "MSPUS":        [329000, 329000, 334000, None,   369000, None],
        "MORTGAGE30US": [3.62,   3.62,   3.23,   2.96,   2.74,   3.18],
        "HOUST":        [1567,   1567,   None,   1496,   1680,   1576],
        "CSUSHPINSA":   [213.0,  213.0,  216.0,  218.0,  226.0,  230.0],
        "RHORUSQ156N":  [65.3,   65.3,   67.9,   66.6,   65.5,   65.4],
        "MSACSR":       [3.5,    3.5,    3.3,    4.6,    3.8,    4.5],
    })


@pytest.fixture
def census_raw():
    """
    Sample Census ACS data mimicking the real API response.
    Includes -666666666 sentinel values (suppressed data) and
    a duplicate row to test deduplication.
    """
    return pd.DataFrame({
        "state_name":              ["Alabama", "California", "Iowa", "Alabama", "Hawaii"],
        "state_fips":              ["01", "06", "19", "01", "15"],
        "year":                    [2020, 2020, 2020, 2020, 2020],
        "median_household_income": [52035, 80440, 61691, 52035, 83102],
        "median_home_value":       [154600, 568500, 160700, 154600, -666666666],
        "median_gross_rent":       [783, 1614, 786, 783, 1748],
        "total_occupied_units":    [1894032, 13157673, 1268408, 1894032, 455338],
        "owner_occupied_units":    [1199381, 6749498, 882697, 1199381, 247537],
        "renter_occupied_units":   [694651, 6408175, 385711, 694651, 207801],
        "total_population":        [4921532, 39538223, 3190369, 4921532, 1455271],
        "homeownership_rate":      [63.3, 51.3, 69.6, 63.3, 54.4],
        "price_to_income_ratio":   [2.97, 7.07, 2.60, 2.97, -666666666],
    })


@pytest.fixture
def zillow_raw():
    """
    Sample Zillow ZHVI data in long format (already reshaped).
    Includes a missing zhvi value and a duplicate row.
    """
    return pd.DataFrame({
        "RegionName": ["Alabama", "Alabama", "Alabama", "California", "California", "Iowa", "Iowa"],
        "date": pd.to_datetime([
            "2020-01-31", "2020-01-31",  # dupe
            "2020-06-30",
            "2020-01-31", "2020-06-30",
            "2020-01-31", "2020-06-30",
        ]),
        "zhvi": [154200, 154200, 158900, 562100, None, 161400, 165800],
    })


@pytest.fixture
def clean_fred_df(fred_raw):
    """Pre-cleaned FRED data for use in merge tests."""
    return clean_fred(fred_raw)


@pytest.fixture
def clean_census_df(census_raw):
    """Pre-cleaned Census data for use in merge tests."""
    return clean_census(census_raw)


@pytest.fixture
def clean_zillow_df(zillow_raw):
    """Pre-cleaned Zillow data for use in merge tests."""
    return clean_zillow(zillow_raw)


# Data Loading Tests

class TestDataLoading:

    def test_fred_has_required_columns(self, fred_raw):
        """FRED data should have a date column and at least one series column."""
        assert "date" in fred_raw.columns
        assert "MSPUS" in fred_raw.columns
        assert "MORTGAGE30US" in fred_raw.columns

    def test_census_has_required_columns(self, census_raw):
        """Census data should have state, year, income, and home value columns."""
        required = ["state_name", "year", "median_household_income", "median_home_value"]
        for col in required:
            assert col in census_raw.columns

    def test_zillow_has_required_columns(self, zillow_raw):
        """Zillow data should have RegionName, date, and zhvi columns."""
        assert "RegionName" in zillow_raw.columns
        assert "date" in zillow_raw.columns
        assert "zhvi" in zillow_raw.columns


# Data Cleaning Tests

class TestCleanFred:

    def test_removes_duplicates(self, fred_raw):
        """clean_fred should remove duplicate rows."""
        assert fred_raw.duplicated().sum() > 0
        cleaned = clean_fred(fred_raw)
        assert cleaned.duplicated().sum() == 0

    def test_date_parsed_as_datetime(self, fred_raw):
        """clean_fred should convert the date column to datetime."""
        cleaned = clean_fred(fred_raw)
        assert pd.api.types.is_datetime64_any_dtype(cleaned["date"])

    def test_numeric_columns_are_float(self, fred_raw):
        """clean_fred should convert all non-date columns to numeric."""
        cleaned = clean_fred(fred_raw)
        for col in cleaned.columns:
            if col != "date":
                assert pd.api.types.is_numeric_dtype(cleaned[col])

    def test_sorted_by_date(self, fred_raw):
        """clean_fred should return rows sorted chronologically."""
        cleaned = clean_fred(fred_raw)
        assert cleaned["date"].is_monotonic_increasing


class TestCleanCensus:

    def test_removes_duplicates(self, census_raw):
        """clean_census should remove duplicate rows."""
        assert census_raw.duplicated().sum() > 0
        cleaned = clean_census(census_raw)
        assert cleaned.duplicated().sum() == 0

    def test_replaces_sentinel_value(self, census_raw):
        """clean_census should replace -666666666 with NaN."""
        assert (census_raw == -666666666).any().any()
        cleaned = clean_census(census_raw)
        assert not (cleaned == -666666666).any().any()

    def test_drops_rows_missing_income(self, census_raw):
        """clean_census should drop rows where income is null after sentinel replacement."""
        cleaned = clean_census(census_raw)
        assert cleaned["median_household_income"].isna().sum() == 0

    def test_drops_rows_missing_home_value(self, census_raw):
        """clean_census should drop rows where home value is null after sentinel replacement."""
        cleaned = clean_census(census_raw)
        assert cleaned["median_home_value"].isna().sum() == 0


class TestCleanZillow:

    def test_removes_duplicates(self, zillow_raw):
        """clean_zillow should remove duplicate rows."""
        assert zillow_raw.duplicated().sum() > 0
        cleaned = clean_zillow(zillow_raw)
        assert cleaned.duplicated().sum() == 0

    def test_drops_missing_zhvi(self, zillow_raw):
        """clean_zillow should drop rows where zhvi is null."""
        assert zillow_raw["zhvi"].isna().sum() > 0
        cleaned = clean_zillow(zillow_raw)
        assert cleaned["zhvi"].isna().sum() == 0

    def test_date_parsed_as_datetime(self, zillow_raw):
        """clean_zillow should ensure date column is datetime."""
        cleaned = clean_zillow(zillow_raw)
        assert pd.api.types.is_datetime64_any_dtype(cleaned["date"])


# Merge Logic Tests

class TestMerge:

    def test_merged_is_not_empty(self, clean_fred_df, clean_census_df, clean_zillow_df):
        """merge_all should produce a non-empty dataset."""
        merged = merge_all(clean_fred_df, clean_census_df, clean_zillow_df)
        assert len(merged) > 0

    def test_merged_has_price_to_income_ratio(self, clean_fred_df, clean_census_df, clean_zillow_df):
        """merge_all should compute and include price_to_income_ratio column."""
        merged = merge_all(clean_fred_df, clean_census_df, clean_zillow_df)
        assert "price_to_income_ratio" in merged.columns

    def test_merged_has_year_column(self, clean_fred_df, clean_census_df, clean_zillow_df):
        """merge_all should include a year column."""
        merged = merge_all(clean_fred_df, clean_census_df, clean_zillow_df)
        assert "year" in merged.columns

    def test_merged_has_zhvi_column(self, clean_fred_df, clean_census_df, clean_zillow_df):
        """merge_all should include zhvi from Zillow."""
        merged = merge_all(clean_fred_df, clean_census_df, clean_zillow_df)
        assert "zhvi" in merged.columns

    def test_merged_has_mortgage_rate(self, clean_fred_df, clean_census_df, clean_zillow_df):
        """merge_all should attach FRED mortgage rate to state rows."""
        merged = merge_all(clean_fred_df, clean_census_df, clean_zillow_df)
        assert "MORTGAGE30US" in merged.columns


# Data Validation Tests

class TestValidation:

    def test_price_to_income_ratio_is_positive(self, clean_fred_df, clean_census_df, clean_zillow_df):
        """price_to_income_ratio should always be positive where not null."""
        merged = merge_all(clean_fred_df, clean_census_df, clean_zillow_df)
        valid = merged["price_to_income_ratio"].dropna()
        assert (valid > 0).all()

    def test_zhvi_is_positive(self, clean_fred_df, clean_census_df, clean_zillow_df):
        """zhvi values should be positive."""
        merged = merge_all(clean_fred_df, clean_census_df, clean_zillow_df)
        valid = merged["zhvi"].dropna()
        assert (valid > 0).all()

    def test_no_sentinel_values_in_merged(self, clean_fred_df, clean_census_df, clean_zillow_df):
        """No -666666666 sentinel values should appear in the merged dataset."""
        merged = merge_all(clean_fred_df, clean_census_df, clean_zillow_df)
        numeric_cols = merged.select_dtypes(include="number").columns
        assert not (merged[numeric_cols] == -666666666).any().any()

    def test_state_names_not_null(self, clean_fred_df, clean_census_df, clean_zillow_df):
        """All rows in merged dataset should have a state name."""
        merged = merge_all(clean_fred_df, clean_census_df, clean_zillow_df)
        assert merged["state_name"].notna().all()


# API Fetch Tests (mocked so no real API calls are made)

class TestFetchFred:

    @patch("fetch_fred.requests.get")
    def test_fetch_fred_series_returns_dataframe(self, mock_get):
        """fetch_fred_series should return a DataFrame with date and series columns."""
        from fetch_fred import fetch_fred_series

        # mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "observations": [
                {"date": "2020-01-01", "value": "329000"},
                {"date": "2020-04-01", "value": "334000"},
                {"date": "2020-07-01", "value": "."},  # FRED missing value
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        df = fetch_fred_series("MSPUS", api_key="test_key")

        assert "date" in df.columns
        assert "MSPUS" in df.columns
        assert len(df) == 3

    @patch("fetch_fred.requests.get")
    def test_fetch_fred_converts_missing_values(self, mock_get):
        """fetch_fred_series should convert FRED '.' missing values to NaN."""
        from fetch_fred import fetch_fred_series

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "observations": [
                {"date": "2020-01-01", "value": "329000"},
                {"date": "2020-04-01", "value": "."},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        df = fetch_fred_series("MSPUS", api_key="test_key")

        assert df["MSPUS"].isna().sum() == 1
        assert df["MSPUS"].iloc[0] == 329000.0

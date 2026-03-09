"""Tests for ETL modules: extract, transform, load, database."""
import os
import sqlite3
import tempfile
import pandas as pd
import pytest
from src.etl.extract import extract_city, find_files, REQUIRED_COLUMNS, COL_DISTANCE, COL_AVG_SPEED, COL_MAX_SPEED
from src.etl.transform import convert_to_01, build_summary, renumber_units
from src.etl.load import export_report
from src.etl.database import create_connection, load_trips


# --- extract tests ---

def test_extract_city_standard():
    assert extract_city("CELAYA-DIC 2021.xlsx") == "CELAYA"


def test_extract_city_volvo():
    assert extract_city("VOLVO QUERETARO-ENERO 2022.xlsx") == "QUERETARO"


def test_extract_city_double_space():
    assert extract_city("S.L.P.  DIC 2021.xlsx") == "S.L.P."


def test_extract_city_dot_enero():
    assert extract_city("SILAO.ENERO 2022.xlsx") == "SILAO"


# --- transform tests ---

def _make_trip_df(n: int = 5, off_hours: str = "no") -> pd.DataFrame:
    """Helper: create a minimal trip DataFrame."""
    return pd.DataFrame({
        COL_DISTANCE: [100.0] * n,
        COL_AVG_SPEED: [50.0] * n,
        COL_MAX_SPEED: [80.0] * n,
        "off_hours": [off_hours] * n,
        "unit": ["UNIT-01"] * n,
        "agency": ["CELAYA"] * n,
    })


def test_convert_to_01_basic():
    df = _make_trip_df(3, "yes")
    result = convert_to_01(df, "off_hours")
    assert (result["off_hours"] == 1).all()


def test_convert_to_01_already_numeric():
    df = _make_trip_df(3)
    df["off_hours"] = 0
    result = convert_to_01(df, "off_hours")
    assert (result["off_hours"] == 0).all()


def test_convert_to_01_nan_values():
    df = _make_trip_df(3)
    df.loc[0, "off_hours"] = None
    result = convert_to_01(df, "off_hours")
    assert result["off_hours"].iloc[0] == 0


def test_convert_to_01_unexpected_values():
    df = _make_trip_df(3)
    df.loc[0, "off_hours"] = "maybe"
    result = convert_to_01(df, "off_hours")
    assert result["off_hours"].iloc[0] == 0


def test_build_summary_basic():
    df = _make_trip_df(5)
    summary = build_summary(df)
    assert len(summary) == 1
    assert summary["distance_km"].iloc[0] == 500.0
    assert summary["total_trips"].iloc[0] == 5
    assert summary["liters"].iloc[0] > 0
    assert summary["cost"].iloc[0] > 0
    assert summary["status"].iloc[0] == "green"


def test_build_summary_night_metrics():
    df = _make_trip_df(3, "yes")
    summary = build_summary(df)
    assert summary["distance_night"].iloc[0] == 300.0
    assert summary["cost_night"].iloc[0] > 0


def test_build_summary_no_night():
    df = _make_trip_df(3, "no")
    summary = build_summary(df)
    assert summary["distance_night"].iloc[0] == 0


def test_renumber_units():
    df = pd.DataFrame({
        "unit": ["A", "A", "B", "B"],
        "agency": ["X", "X", "Y", "Y"],
    })
    result = renumber_units(df)
    assert result["unit"].iloc[0] == "UNIT-01"
    assert result["unit"].iloc[2] == "UNIT-02"


# --- load tests ---

def test_export_report_creates_file():
    df = _make_trip_df(3)
    df["date"] = pd.Timestamp("2022-01-01")
    df["day"] = "Saturday"
    df["month"] = "January"
    df["year"] = 2022
    df["start_time"] = "08:00"
    df["end_time"] = "09:00"
    df["travel_time_min"] = 30.0
    df["idle_time_min"] = 10.0

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name

    try:
        result = export_report(df, path)
        assert os.path.exists(result)
        df_read = pd.read_excel(result, sheet_name="data")
        assert len(df_read) == 3
    finally:
        os.unlink(path)


# --- database tests ---

def test_create_connection_memory():
    conn = create_connection(":memory:")
    assert conn is not None
    conn.close()


def test_load_trips_and_query():
    conn = sqlite3.connect(":memory:")
    df = _make_trip_df(3)
    df["date"] = "2022-01-01"
    df["day"] = "Saturday"
    df["month"] = "January"
    df["year"] = 2022
    df["start_time"] = "08:00"
    df["end_time"] = "09:00"
    df["travel_time_min"] = 30.0
    df["idle_time_min"] = 10.0

    # Rename columns to match what load_trips expects
    df = df.rename(columns={
        COL_DISTANCE: "distance_km",
        COL_AVG_SPEED: "avg_speed_kmh",
        COL_MAX_SPEED: "max_speed_kmh",
    })

    load_trips(conn, df)
    result = pd.read_sql("SELECT COUNT(*) AS n FROM trips", conn)
    assert result["n"].iloc[0] == 3
    conn.close()


def test_load_trips_replaces_data():
    conn = sqlite3.connect(":memory:")
    df = _make_trip_df(2)
    df["date"] = "2022-01-01"
    df["day"] = "Saturday"
    df["month"] = "January"
    df["year"] = 2022
    df["start_time"] = "08:00"
    df["end_time"] = "09:00"
    df["travel_time_min"] = 30.0
    df["idle_time_min"] = 10.0
    df = df.rename(columns={
        COL_DISTANCE: "distance_km",
        COL_AVG_SPEED: "avg_speed_kmh",
        COL_MAX_SPEED: "max_speed_kmh",
    })

    load_trips(conn, df)
    load_trips(conn, df)  # second call should replace, not duplicate
    result = pd.read_sql("SELECT COUNT(*) AS n FROM trips", conn)
    assert result["n"].iloc[0] == 2
    conn.close()

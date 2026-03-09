"""Tests for dashboard query helpers."""
import sqlite3
import pytest
from src.dashboard.queries import build_where, get_kpis


@pytest.fixture
def db():
    """Create an in-memory SQLite with sample trip data."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE trips (
            unit TEXT, agency TEXT, month TEXT, date TEXT, day TEXT,
            distance_km REAL, avg_speed REAL, max_speed REAL,
            off_hours TEXT, idle_time_min REAL
        )
    """)
    rows = [
        ("UNIT-01", "CELAYA", "January", "2022-01-05", "Wednesday", 100.0, 50.0, 80.0, "no", 30.0),
        ("UNIT-01", "CELAYA", "January", "2022-01-06", "Thursday", 200.0, 60.0, 90.0, "yes", 45.0),
        ("UNIT-02", "QUERETARO", "December", "2021-12-10", "Friday", 150.0, 55.0, 85.0, "no", 20.0),
    ]
    conn.executemany(
        "INSERT INTO trips VALUES (?,?,?,?,?,?,?,?,?,?)", rows
    )
    conn.commit()
    yield conn
    conn.close()


# --- build_where tests ---

def test_build_where_no_filters():
    where, params = build_where([], [], "Todos")
    assert where == ""
    assert params == []


def test_build_where_agency_filter():
    where, params = build_where(["CELAYA"], [], "Todos")
    assert "agency IN (?)" in where
    assert params == ["CELAYA"]


def test_build_where_multiple_agencies():
    where, params = build_where(["CELAYA", "QUERETARO"], [], "Todos")
    assert "agency IN (?,?)" in where
    assert params == ["CELAYA", "QUERETARO"]


def test_build_where_month_filter():
    where, params = build_where([], ["January"], "Todos")
    assert "month IN (?)" in where
    assert params == ["January"]


def test_build_where_off_hours():
    where, params = build_where([], [], "Fuera de horario")
    assert "off_hours = 'yes'" in where
    assert params == []


def test_build_where_in_hours():
    where, params = build_where([], [], "Dentro de horario")
    assert "off_hours = 'no'" in where


def test_build_where_combined():
    where, params = build_where(["CELAYA"], ["January"], "Fuera de horario")
    assert "agency IN (?)" in where
    assert "month IN (?)" in where
    assert "off_hours = 'yes'" in where
    assert params == ["CELAYA", "January"]


# --- get_kpis tests ---

def test_get_kpis_no_filter(db):
    result = get_kpis(db)
    assert len(result) == 1
    assert result["total_cost"].iloc[0] > 0
    assert result["total_liters"].iloc[0] > 0


def test_get_kpis_with_filter(db):
    where, params = build_where(["CELAYA"], [], "Todos")
    result = get_kpis(db, where, params)
    assert result["total_cost"].iloc[0] > 0

    where_all, params_all = build_where([], [], "Todos")
    result_all = get_kpis(db, where_all, params_all)
    assert result["total_cost"].iloc[0] < result_all["total_cost"].iloc[0]

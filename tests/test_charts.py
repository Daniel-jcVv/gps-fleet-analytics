"""Tests for chart factory."""
import pandas as pd
from src.dashboard.charts import make_chart, cap_rows


def test_cap_rows_under_limit():
    df = pd.DataFrame({"a": range(5)})
    assert len(cap_rows(df, limit=10)) == 5


def test_cap_rows_over_limit():
    df = pd.DataFrame({"a": range(20)})
    assert len(cap_rows(df, limit=10)) == 10


def test_make_chart_bar_h():
    df = pd.DataFrame({"Agencia": ["CELAYA", "QUERETARO"], "Costo": [1000, 2000]})
    fig = make_chart(df, chart_type="bar_h", title="Test")
    assert fig is not None
    assert fig.layout.title.text == "Test"


def test_make_chart_donut():
    df = pd.DataFrame({"Agencia": ["CELAYA", "QUERETARO"], "Viajes": [10, 20]})
    fig = make_chart(df, chart_type="donut", title="Donut")
    assert fig is not None


def test_make_chart_empty_numeric():
    df = pd.DataFrame({"a": ["x", "y"], "b": ["z", "w"]})
    fig = make_chart(df, chart_type="bar_h")
    assert fig is None


def test_make_chart_line():
    df = pd.DataFrame({
        "Fecha": ["2022-01-01", "2022-01-02"],
        "Mes": ["January", "January"],
        "Costo": [500, 600],
    })
    fig = make_chart(df, chart_type="line", title="Trend")
    assert fig is not None

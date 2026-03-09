import sqlite3
import pandas as pd
from src.etl.extract import FUEL_EFFICIENCY_KM_PER_LITER, FUEL_PRICE_PER_LITER

FE = FUEL_EFFICIENCY_KM_PER_LITER
FP = FUEL_PRICE_PER_LITER


def build_where(
    sel_agencies: list[str],
    sel_months: list[str],
    sel_horario: str,
) -> tuple[str, list[str]]:
    """Build WHERE clause and params from filter selections."""
    clauses: list[str] = []
    params: list[str] = []
    if sel_agencies:
        placeholders = ",".join("?" for _ in sel_agencies)
        clauses.append(f"agency IN ({placeholders})")
        params.extend(sel_agencies)
    if sel_months:
        placeholders = ",".join("?" for _ in sel_months)
        clauses.append(f"month IN ({placeholders})")
        params.extend(sel_months)
    if sel_horario == "Dentro de horario":
        clauses.append("off_hours = 'no'")
    elif sel_horario == "Fuera de horario":
        clauses.append("off_hours = 'yes'")
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params


def get_agencies(conn: sqlite3.Connection) -> list[str]:
    """Return sorted list of unique agencies."""
    return pd.read_sql(
        "SELECT DISTINCT agency FROM trips ORDER BY agency", conn
    )["agency"].tolist()


def get_kpis(
    conn: sqlite3.Connection,
    where: str = "",
    params: list[str] | None = None,
) -> pd.DataFrame:
    """Return KPI metrics filtered by where clause."""
    return pd.read_sql(f"""
        SELECT
            ROUND((SUM(distance_km) / {FE}) * {FP}, 0) AS total_cost,
            ROUND(SUM(CASE WHEN off_hours = 'yes' THEN distance_km ELSE 0 END) / {FE} * {FP}, 0) AS off_hours_cost,
            ROUND(SUM(distance_km) / {FE}, 0) AS total_liters,
            ROUND(SUM(distance_km) / {FE} * {FP} / MAX(COUNT(DISTINCT unit), 1), 0) AS cost_per_unit,
            ROUND(SUM(distance_km) / {FE} * {FP} / MAX(COUNT(*), 1), 2) AS cost_per_trip
        FROM trips {where}
    """, conn, params=params)


def get_cost_by_agency(
    conn: sqlite3.Connection,
    where: str = "",
    params: list[str] | None = None,
) -> pd.DataFrame:
    return pd.read_sql(f"""
        SELECT REPLACE(agency, 'AGUASCALIENTES', 'AGS') AS Agencia,
            ROUND((SUM(distance_km) / {FE}) * {FP}, 0) AS 'Costo MXN'
        FROM trips {where} GROUP BY agency ORDER BY 'Costo MXN' DESC
    """, conn, params=params)


def get_off_hours_by_agency(
    conn: sqlite3.Connection,
    where: str = "",
    params: list[str] | None = None,
) -> pd.DataFrame:
    return pd.read_sql(f"""
        SELECT REPLACE(agency, 'AGUASCALIENTES', 'AGS') AS Agencia,
            COUNT(*) AS Viajes
        FROM trips {where} {"AND" if where else "WHERE"} off_hours = 'yes'
        GROUP BY agency ORDER BY Viajes DESC
    """, conn, params=params)


def get_idle_heatmap(
    conn: sqlite3.Connection,
    where: str = "",
    params: list[str] | None = None,
) -> pd.DataFrame:
    return pd.read_sql(f"""
        SELECT REPLACE(agency, 'AGUASCALIENTES', 'AGS') AS Agencia, day AS Dia,
            ROUND(SUM(idle_time_min) / 60, 0) AS Horas
        FROM trips {where} GROUP BY agency, day
    """, conn, params=params)


def get_daily_cost_trend(
    conn: sqlite3.Connection,
    where: str = "",
    params: list[str] | None = None,
) -> pd.DataFrame:
    return pd.read_sql(f"""
        SELECT date AS Fecha, month AS Mes,
            ROUND((SUM(distance_km) / {FE}) * {FP}, 0) AS 'Costo MXN'
        FROM trips {where} GROUP BY date ORDER BY date
    """, conn, params=params)

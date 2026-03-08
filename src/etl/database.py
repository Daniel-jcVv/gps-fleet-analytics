import sqlite3
import pandas as pd

DB_PATH = "data_gps/fleet.db"


def create_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    return conn


def load_trips(conn, df):
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit TEXT,
            agency TEXT,
            date TEXT,
            day TEXT,
            month TEXT,
            year INTEGER,
            start_time TEXT,
            end_time TEXT,
            off_hours TEXT,
            distance_km REAL,
            avg_speed_kmh REAL,
            max_speed_kmh REAL,
            travel_time_min REAL,
            idle_time_min REAL
        )
    """)
    conn.commit()

    col_map = {     
        "Distancia recorrida total,\nkm": "distance_km",
        "Velocidad media,\nkm/h": "avg_speed_kmh",
        "Max. velocidad,\nkm/h": "max_speed_kmh",
    }
    df = df.rename(columns=col_map)

    cols = ["unit", "agency", "date", "day", "month", "year",
        "start_time", "end_time", "off_hours",
        "distance_km", "avg_speed_kmh", "max_speed_kmh",
        "travel_time_min", "idle_time_min"]
    df = df[cols]
    df["date"] = df["date"].astype(str)

    conn.cursor().execute("DELETE FROM trips")
    conn.commit()
    df.to_sql("trips", conn, if_exists="append", index=False)



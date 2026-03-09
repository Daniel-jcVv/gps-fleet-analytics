import os
import sqlite3
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def _default_db_path() -> str:
    """Use /tmp on Streamlit Cloud (read-only filesystem), local path otherwise."""
    if os.getenv("STREAMLIT_SERVER_HEADLESS"):
        return "/tmp/fleet.db"
    return "data_gps/fleet.db"

DB_PATH = os.getenv("GPS_DB_PATH", _default_db_path())


def create_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create and return a SQLite connection."""
    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as e:
        raise ConnectionError(f"Cannot connect to database '{db_path}': {e}") from e
    return conn


def load_trips(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    """Load trip DataFrame into the trips table. Replaces existing data."""
    conn.execute("""
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

    conn.execute("DELETE FROM trips")
    conn.commit()
    df.to_sql("trips", conn, if_exists="append", index=False)
    logger.info("Loaded %d trips into database", len(df))


def ensure_db(db_path: str = DB_PATH) -> None:
    """Run the ETL pipeline to create fleet.db if it doesn't exist."""
    if os.path.exists(db_path):
        return

    logger.info("Database not found at '%s' — building from raw Excel files...", db_path)

    from .extract import process_file, extract_city, find_files, CITY_CODES
    from .transform import renumber_units

    files = find_files()
    if not files:
        raise FileNotFoundError("No raw Excel files found in data folders")

    all_trips = []
    for f in files:
        agency = extract_city(f)
        if agency not in CITY_CODES:
            logger.warning("Skipping unknown city '%s' in %s", agency, f)
            continue
        try:
            df = process_file(f, agency)
            all_trips.append(df)
        except Exception as e:
            logger.warning("Failed to process '%s': %s", f, e)

    if not all_trips:
        raise RuntimeError("No trips could be processed from raw files")

    df_master = pd.concat(all_trips, ignore_index=True)
    df_master = renumber_units(df_master)

    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = create_connection(db_path)
    try:
        load_trips(conn, df_master)
    finally:
        conn.close()

    logger.info("Database created at '%s' with %d trips", db_path, len(df_master))

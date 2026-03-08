import os
import glob
import pandas as pd
from openpyxl import load_workbook

# Constants (source: docs/BUSINESS_RULES.md)
FUEL_EFFICIENCY_KM_PER_LITER = 17.23
FUEL_PRICE_PER_LITER = 23.24

# Raw column names
COL_DISTANCE  = "Distancia recorrida total,\nkm"
COL_AVG_SPEED = "Velocidad media,\nkm/h"
COL_MAX_SPEED = "Max. velocidad,\nkm/h"
COL_START     = "Inicio de movimiento"
COL_END       = "Final de movimiento"

# City name → short code
CITY_CODES = {
    "AGUASCALIENTES": "ags",
    "CELAYA":         "cel",
    "QUERETARO":      "qro",
    "SAN JUAN":       "snjuan",
    "SILAO":          "silao",
    "S.L.P.":         "slp",
    "TOLUCA":         "tol",
    "ZACATECAS":      "zac",
}

DATA_FOLDERS = [
    "data_gps/dic_2021",
    "data_gps/ene_2022",
]

# Spanish month abbreviations → month number
MONTHS_ES = {
    "ene": "01", "feb": "02", "mar": "03", "abr": "04",
    "may": "05", "jun": "06", "jul": "07", "ago": "08",
    "sep": "09", "oct": "10", "nov": "11", "dic": "12",
}


def extract_city(file_path):
    """Extract city name from filename. Handles 'VOLVO CITY-MES' and 'CITY-MES' formats."""
    name = os.path.basename(file_path).replace("VOLVO ", "")
    for suffix in ["-DIC 2021", "  DIC 2021", "-ENERO 2022", ".ENERO 2022", "- ENERO 2022"]:
        name = name.replace(suffix, "")
    return name.replace(".xlsx", "").strip()


def find_files():
    """Find all raw Excel files in DATA_FOLDERS."""
    files = []
    for folder in DATA_FOLDERS:
        files += glob.glob(os.path.join(folder, "*.xlsx"))
    return files


def _extract_time_string(col):
    """Extract 'HH:MM' from strings like '10:29 - Calle Villas...'"""
    return col.str.split(" - ").str[0]


def process_file(file_path, agency):
    """Read Excel, clean data, return DataFrame with all trips.
    
    Each row = one trip. Columns include date, day, month, agency, unit,
    start_hour, end_hour, off_hours, distance, speed metrics.
    """
    wb = load_workbook(file_path, read_only=True)
    sheets = wb.sheetnames
    wb.close()

    frames = []
    for sheet in sheets:
        if sheet == sheets[0] or sheet.endswith(" - 2"):
            continue

        df = pd.read_excel(file_path, sheet_name=sheet, header=4, usecols="A:G")

        # --- Extract date from grouped header rows ---
        # Header rows look like: "01-ene-2022 (Mié.) : 10"
        # They have no distance value — we extract the date and ffill to trip rows below
        date_mask  = df[COL_START].astype(str).str.match(r"^\d{2}-\w+-\d{4}")
        raw_dates  = df.loc[date_mask, COL_START].str.extract(r"^(\d{2})-(\w+)-(\d{4})")
        normalized = raw_dates[0] + "-" + raw_dates[1].str.lower().map(MONTHS_ES) + "-" + raw_dates[2]
        df["date"] = pd.to_datetime(normalized, format="%d-%m-%Y")
        df["date"] = df["date"].ffill()

        # --- Filter actual trip rows ---
        df = df.dropna(subset=[COL_START, COL_END, COL_DISTANCE])
        df = df[~df[COL_START].astype(str).str.contains("En total")]

        # --- Derive temporal columns from date ---
        df["day"]   = df["date"].dt.day_name()
        df["month"] = df["date"].dt.month_name()
        df["year"]  = df["date"].dt.year

        # --- Extract time strings (keep full HH:MM format) ---
        df["start_time"] = _extract_time_string(df[COL_START])
        df["end_time"]   = _extract_time_string(df[COL_END])

        # --- Off-hours flag (after 19:00 or before 05:00) ---
        start_h = pd.to_datetime(df["start_time"], format="mixed").dt.hour
        end_h   = pd.to_datetime(df["end_time"],   format="mixed").dt.hour
        df["off_hours"] = ((start_h >= 19) | (end_h <= 5)).map({True: "yes", False: "no"})

        # --- Convert timedelta to minutes ---
        df["travel_time_min"] = df["Tiempo de viaje"] / pd.Timedelta(minutes=1)
        df["idle_time_min"] = df["Tiempo de inactividad"] / pd.Timedelta(minutes=1)

        # --- Identity columns ---
        df["unit"]   = sheet  # anonymized (UNIT-XX)
        df["agency"] = agency

        frames.append(df)

    return pd.concat(frames, ignore_index=True)

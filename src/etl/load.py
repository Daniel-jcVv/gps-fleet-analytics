import pandas as pd
from .extract import COL_DISTANCE, COL_AVG_SPEED, COL_MAX_SPEED

# Columns to include in the "data" sheet (trip-level, matches MASTER original)
DATA_COLUMNS = [
    "agency", "unit", "date", "day", "month", "year",
    "start_time", "end_time",
    COL_DISTANCE, COL_AVG_SPEED, COL_MAX_SPEED,
    "off_hours", "travel_time_min", "idle_time_min"
]


def export_report(df_trips, output_path):
    """Export trip-level data to Excel with single 'data' sheet."""
    # --- Sheet: data ---
    cols = [c for c in DATA_COLUMNS if c in df_trips.columns]
    df_data = df_trips[cols].copy()
    df_data = df_data.rename(columns={
        "Distancia recorrida total,\nkm": "distance_km",
        "Velocidad media,\nkm/h":        "avg_speed_kmh",
        "Max. velocidad,\nkm/h":         "max_speed_kmh",
    })
    df_data.columns = [c.replace("\n", " ") for c in df_data.columns]

    # Format date as DD/MM/YYYY
    df_data["date"] = df_data["date"].apply(
        lambda d: d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else d
    )

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_data.to_excel(writer, sheet_name="data", index=False)

    return output_path


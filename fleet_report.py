import os
import warnings
import pandas as pd
import glob
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

FUEL_EFFICIENCY_KM_PER_LITER = 17.23 # average km per liter
FUEL_PRICE_PER_LITER = 21.5 # average price per liter


def process_file(file_path):
    """Read Excel, clean data, and return a DataFrame with all trips."""

    # Load the Excel file
    wb = load_workbook(file_path, read_only=True)
    sheets = wb.sheetnames
    wb.close()

    # read each sheet into a dataframe and concatenate them
    frames = []
    for sheet in sheets:
        # skip first sheet and sheets ending with " - 2"
        if sheet == sheets[0] or sheet.endswith(" - 2"):
            continue

        # read each sheet into a dataframe
        df = pd.read_excel(
            file_path,
            sheet_name=sheet,
            header=4,
            usecols="A:G"
        )

        # drop rows where "Inicio de movimiento" is NaN
        df = df.dropna(subset=["Inicio de movimiento"])
        # drop rows where "Distancia recorrida total, km" is NaN
        df = df.dropna(subset=["Distancia recorrida total,\nkm"])
        df["unit"] = sheet # add a column for the unit (sheet name)
        frames.append(df)
    
    # concatenate all dataframes into one
    df_total = pd.concat(frames, ignore_index=True)
    return df_total


def build_summary(df):
    """Group by unit, calculate metrics, fuel, traffic light"""
    group_by_unit = df.groupby("unit").agg(
        {
            "Distancia recorrida total,\nkm": "sum",
            "Velocidad media,\nkm/h": "mean",
            "Max. velocidad,\nkm/h": "max"
        }
    )
    group_by_unit["liters"] = group_by_unit["Distancia recorrida total,\nkm"] / FUEL_EFFICIENCY_KM_PER_LITER
    group_by_unit["cost"] = group_by_unit["liters"] * FUEL_PRICE_PER_LITER
    group_by_unit.sort_values("cost", ascending=False)

    # traffic light rules
    def traffic_light(km):
        if km < 3000:
            return "green"
        elif km <= 6000:
            return "yellow"
        else:
            return "red"
        
    # apply traffic light function to distance column    
    group_by_unit["status"] = group_by_unit["Distancia recorrida total,\nkm"].apply(traffic_light)
    group_by_unit.sort_values("Distancia recorrida total,\nkm", ascending=False)
    return group_by_unit


def export_report(df, output_path):
    """Export to Excel with multiple sheets and formatting """
    # rename columns for better readability
    group_by_unit = df.rename(columns={
        "Distancia recorrida total,\nkm": "distance_km",
        "Velocidad media,\nkm/h": "avg_speed_kmh",
        "Max. velocidad,\nkm/h": "max_speed_kmh"
    })
    
    # export to excel
    group_by_unit.sort_values("cost", ascending=False).to_excel(output_path, sheet_name="summary")
    # apply traffic light formatting
    wb = load_workbook(output_path)
    ws = wb["summary"]

    # define fill colors
    fill_colors = {
        "green": PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"),
        "yellow": PatternFill(start_color="FFEB96", end_color="FFEB9C", fill_type="solid"),
        "red": PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    }

    # apply fill colors based on status, status is in column G, data starts from row 2
    for row in range(2, ws.max_row + 1):
        status = ws.cell(row=row, column=7).value
        if status in fill_colors:
            fill = PatternFill(start_color=fill_colors[status].start_color, end_color=fill_colors[status].end_color, fill_type="solid")
            for col in range(1, ws.max_column + 1):
                ws.cell(row=row, column=col).fill = fill

    wb.save(output_path)
    return output_path


CITY_CODES = {
    "AGUASCALIENTES": "ags",
    "CELAYA": "cel",
    "QUERETARO": "qro",
    "SAN JUAN": "snjuan",
    "SILAO": "silao",
    "S.L.P.": "slp",
    "TOLUCA": "tol",
    "ZACATECAS": "zac",
}

DATA_FOLDERS = [
    "data_gps/dic_2021",
    "data_gps/ene_2022",
]


def extract_city(file_path):
    """Extract city name from filename. Handles both 'VOLVO CITY-MES' and 'CITY-MES' formats."""
    name = os.path.basename(file_path).replace("VOLVO ", "")
    # remove period and year suffixes
    for suffix in ["-DIC 2021", "  DIC 2021", "-ENERO 2022", ".ENERO 2022", "- ENERO 2022"]:
        name = name.replace(suffix, "")
    name = name.replace(".xlsx", "")
    return name.strip()


def main():
    os.makedirs("data_gps/output", exist_ok=True)

    files = []
    for folder in DATA_FOLDERS:
        files += glob.glob(os.path.join(folder, "*.xlsx"))

    if not files:
        print("Error: No .xlsx files found in data folders")
        return

    processed = 0
    failed = 0

    for f in files:
        city = extract_city(f)
        code = CITY_CODES.get(city)

        if not code:
            print(f"  SKIPPED: Unknown city '{city}' in {os.path.basename(f)}")
            failed += 1
            continue

        try:
            # extract period from folder name (dic_2021, ene_2022)
            period = os.path.basename(os.path.dirname(f))
            df = process_file(f)
            summary = build_summary(df)
            filename = f"fleet_report_{code}_{period}.xlsx"
            output_path = os.path.join("data_gps/output", filename)
            export_report(summary, output_path)
            print(f"  OK: {filename} ({len(df)} trips)")
            processed += 1
        except Exception as e:
            print(f"  FAILED: {os.path.basename(f)} - {e}")
            failed += 1

    print(f"\nDone. {processed} reports saved, {failed} failed.")


if __name__ == "__main__":
    main()
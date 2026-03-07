import os
import glob
import warnings
from src.extract import process_file
from src.load import export_report
from src.database import create_connection, load_trips
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

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


def extract_city(file_path):
    """Extract city name from filename. Handles 'VOLVO CITY-MES' and 'CITY-MES' formats."""
    name = os.path.basename(file_path).replace("VOLVO ", "")
    for suffix in ["-DIC 2021", "  DIC 2021", "-ENERO 2022", ".ENERO 2022", "- ENERO 2022"]:
        name = name.replace(suffix, "")
    return name.replace(".xlsx", "").strip()


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
    all_trips = []
    for f in files:
        agency = extract_city(f)
        code = CITY_CODES.get(agency)

        if not code:
            print(f"  SKIPPED: Unknown city '{agency}' in {os.path.basename(f)}")
            failed += 1
            continue

        try:
            period     = os.path.basename(os.path.dirname(f))
            df_trips   = process_file(f, agency)
            all_trips.append(df_trips)
            filename   = f"fleet_report_{code}_{period}.xlsx"
            output     = os.path.join("data_gps/output", filename)
            export_report(df_trips, output)
            print(f"  OK: {filename} ({len(df_trips)} trips)")
            processed += 1
        except Exception as e:
            print(f"  FAILED: {os.path.basename(f)} - {e}")
            failed += 1

    print(f"\nDone. {processed} reports saved, {failed} failed.")
    print("\n")

    db_path = "data_gps/fleet.db"

    # --- Build master report with all trips ---
    if not all_trips:
        print("No trips processed, skipping master report.")
        return        
    try:
        print("Building master report...")
        df_master = pd.concat(all_trips, ignore_index=True)

        # Create a new DataFrame with unique agency-unit combinations
        df_group_by_unit_agency = df_master[["unit", "agency"]].drop_duplicates().sort_values(["agency", "unit"])
        df_group_by_unit_agency.reset_index(drop=True, inplace=True)
        df_group_by_unit_agency["number_unit"] = ["UNIT-" + str(i+1).zfill(2) for i in df_group_by_unit_agency.index]

        # merge the new unit numbers back to the master DataFrame
        df_master = df_master.merge(df_group_by_unit_agency, on=["agency", "unit"], how="left")
        df_master["unit"] = df_master["number_unit"]
        df_master.drop(columns=["number_unit"], inplace=True)

        export_report(df_master, "data_gps/output/fleet_report_master.xlsx")
        print("  OK: fleet_report_master.xlsx")

        # connection to database sqlite
        conn = create_connection(db_path)
        load_trips(conn, df_master)
        conn.close()
        print("  OK: fleet.db")

    except Exception as e:
        print(f"  FAILED: Error occurred while building master report - {e}")


if __name__ == "__main__":
    main()

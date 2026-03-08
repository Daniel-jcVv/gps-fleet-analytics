import os
import warnings
import pandas as pd
from src.etl.extract import process_file, extract_city, find_files, CITY_CODES
from src.etl.transform import renumber_units
from src.etl.load import export_report
from src.etl.database import create_connection, load_trips

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def main():
    os.makedirs("data_gps/output", exist_ok=True)

    files = find_files()
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
            period = os.path.basename(os.path.dirname(f))
            df_trips = process_file(f, agency)
            all_trips.append(df_trips)
            filename = f"fleet_report_{code}_{period}.xlsx"
            output = os.path.join("data_gps/output", filename)
            export_report(df_trips, output)
            print(f"  OK: {filename} ({len(df_trips)} trips)")
            processed += 1
        except Exception as e:
            print(f"  FAILED: {os.path.basename(f)} - {e}")
            failed += 1

    print(f"\nDone. {processed} reports saved, {failed} failed.\n")

    if not all_trips:
        print("No trips processed, skipping master report.")
        return

    try:
        print("Building master report...")
        df_master = pd.concat(all_trips, ignore_index=True)
        df_master = renumber_units(df_master)

        export_report(df_master, "data_gps/output/fleet_report_master.xlsx")
        print("  OK: fleet_report_master.xlsx")

        conn = create_connection()
        load_trips(conn, df_master)
        conn.close()
        print("  OK: fleet.db")

    except Exception as e:
        print(f"  FAILED: Error building master report - {e}")


if __name__ == "__main__":
    main()

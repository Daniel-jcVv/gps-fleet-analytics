import os
import glob
import warnings
from src.ingestion import process_file
from src.analysis import build_summary
from src.report import export_report

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

    for f in files:
        agency = extract_city(f)
        code   = CITY_CODES.get(agency)

        if not code:
            print(f"  SKIPPED: Unknown city '{agency}' in {os.path.basename(f)}")
            failed += 1
            continue

        try:
            period     = os.path.basename(os.path.dirname(f))
            df_trips   = process_file(f, agency)
            filename   = f"fleet_report_{code}_{period}.xlsx"
            output     = os.path.join("data_gps/output", filename)
            export_report(df_trips, output)
            print(f"  OK: {filename} ({len(df_trips)} trips)")
            processed += 1
        except Exception as e:
            print(f"  FAILED: {os.path.basename(f)} - {e}")
            failed += 1

    print(f"\nDone. {processed} reports saved, {failed} failed.")


if __name__ == "__main__":
    main()

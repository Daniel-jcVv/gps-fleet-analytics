import os
import logging
import warnings
import pandas as pd
from src.etl.extract import process_file, extract_city, find_files, CITY_CODES
from src.etl.transform import renumber_units
from src.etl.load import export_report
from src.etl.database import create_connection, load_trips

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    os.makedirs("data_gps/output", exist_ok=True)

    files = find_files()
    if not files:
        logger.error("No .xlsx files found in data folders")
        return

    processed = 0
    failed = 0
    all_trips: list[pd.DataFrame] = []
    for f in files:
        agency = extract_city(f)
        code = CITY_CODES.get(agency)

        if not code:
            logger.warning("SKIPPED: Unknown city '%s' in %s", agency, os.path.basename(f))
            failed += 1
            continue

        try:
            period = os.path.basename(os.path.dirname(f))
            df_trips = process_file(f, agency)
            all_trips.append(df_trips)
            filename = f"fleet_report_{code}_{period}.xlsx"
            output = os.path.join("data_gps/output", filename)
            export_report(df_trips, output)
            logger.info("OK: %s (%d trips)", filename, len(df_trips))
            processed += 1
        except Exception as e:
            logger.error("FAILED: %s - %s", os.path.basename(f), e)
            failed += 1

    logger.info("Done. %d reports saved, %d failed.", processed, failed)

    if not all_trips:
        logger.warning("No trips processed, skipping master report.")
        return

    try:
        logger.info("Building master report...")
        df_master = pd.concat(all_trips, ignore_index=True)
        df_master = renumber_units(df_master)

        export_report(df_master, "data_gps/output/fleet_report_master.xlsx")
        logger.info("OK: fleet_report_master.xlsx")

        conn = create_connection()
        try:
            load_trips(conn, df_master)
            logger.info("OK: fleet.db")
        finally:
            conn.close()

    except Exception as e:
        logger.error("FAILED: Error building master report - %s", e)


if __name__ == "__main__":
    main()

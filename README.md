# GPS Fleet Analytics

Automated ETL pipeline that processes raw GPS trip data from a Volvo vehicle fleet across 8 cities in Mexico, calculates fuel consumption and cost metrics, and generates Excel reports with traffic-light formatting.

## Problem

A fleet operations team tracked vehicle trips using GPS devices that exported raw Excel files -- one file per city, per month. Each file contained multiple sheets (one per vehicle unit) with trip-level data: start/end times, distance, and speed.

Every month, an analyst had to manually open each file, consolidate sheets, calculate fuel costs, and flag vehicles exceeding distance thresholds. For 15 files across 2 periods, this took hours of repetitive work.

## Solution

A Python script that automates the entire process:

```
Raw Excel files (15 files, 8 cities, 2 periods)
        |
        v
    process_file()     -- Read sheets, clean data, concatenate trips
        |
        v
    build_summary()    -- Group by unit, calculate fuel + cost, apply traffic light
        |
        v
    export_report()    -- Write Excel with color-coded rows
        |
        v
    15 formatted reports in data_gps/output/
```

## What it does

- Reads multi-sheet Excel files (skips summary and duplicate sheets)
- Cleans data: drops rows with missing trip start or distance
- Groups trips by vehicle unit and calculates:
  - Total distance (km)
  - Average and max speed (km/h)
  - Fuel consumed (liters) based on fleet average efficiency
  - Fuel cost (MXN) based on local gas price
- Applies traffic-light rules based on monthly distance thresholds
- Exports formatted Excel reports with green/yellow/red row coloring
- Handles multiple filename formats across periods

## Business rules

| Metric | Value |
|--------|-------|
| Fuel efficiency | 17.23 km/L (fleet average) |
| Gas price | $21.50 MXN/L (Jan 2022) |
| Green | < 3,000 km/month |
| Yellow | 3,000 - 6,000 km/month |
| Red | > 6,000 km/month |

## Data

Real GPS trip data from Volvo fleet vehicles:

- `data_gps/dic_2021/` -- 7 files (Aguascalientes, Celaya, Queretaro, San Juan, Silao, SLP, Zacatecas)
- `data_gps/ene_2022/` -- 8 files (same cities + Toluca)

Each file contains multiple sheets, one per vehicle unit, with columns: trip start, trip end, duration, total distance (km), average speed (km/h), max speed (km/h).

## Tech stack

| Tool | Purpose |
|------|---------|
| Python 3.12 | Core language |
| pandas | Data reading, cleaning, grouping, aggregation |
| openpyxl | Excel formatting (traffic-light colors) |

## Project structure

```
gps-fleet-analytics/
  fleet_report.py        # ETL script (entry point)
  BUSINESS_RULES.md      # Fuel, cost, and threshold rules
  analysis.ipynb         # Exploratory data analysis notebook
  requirements.txt       # Dependencies
  .gitignore
  data_gps/
    dic_2021/            # 7 raw Excel files (Dec 2021)
    ene_2022/            # 8 raw Excel files (Jan 2022)
    output/              # Generated reports (gitignored)
```

## Usage

```bash
python fleet_report.py
```

Output:

```
  OK: fleet_report_ags_dic_2021.xlsx (142 trips)
  OK: fleet_report_cel_dic_2021.xlsx (98 trips)
  ...
  OK: fleet_report_tol_ene_2022.xlsx (67 trips)

Done. 15 reports saved, 0 failed.
```

Reports are saved to `data_gps/output/` with the naming pattern `fleet_report_{city}_{period}.xlsx`.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python fleet_report.py
```

## License

Portfolio project for demonstration purposes.

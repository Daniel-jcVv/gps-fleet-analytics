# GPS Fleet Analytics

ETL pipeline + interactive dashboard that processes raw GPS trip data from a vehicle fleet across 8 cities in Mexico, loads it into SQLite, and visualizes cost and usage patterns through a Streamlit dashboard with AI-powered chat.

## Problem

A fleet operations team tracked vehicle trips using GPS devices that exported raw Excel files -- one file per city, per month. Each file contained multiple sheets (one per vehicle unit) with trip-level data: start/end times, distance, and speed.

Every month, an analyst had to manually open each file, consolidate sheets, calculate fuel costs, and flag vehicles exceeding distance thresholds. For 15 files across 2 periods, this took hours of repetitive work.

## Solution

```
Raw Excel files (15 files, 8 cities, 2 periods)
        |
    extract.py      -- Read sheets, parse dates, extract times, flag off-hours
        |
    transform.py    -- Renumber units, build summary with traffic light
        |
    load.py         -- Export formatted Excel reports
    database.py     -- Load into SQLite (fleet.db)
        |
    app.py          -- Streamlit dashboard with filters, charts, and AI chat
```

## Features

**ETL Pipeline:**
- Reads multi-sheet Excel files (skips summary and duplicate sheets)
- Extracts date, time, off-hours flag, travel time, and idle time
- Calculates fuel consumption and cost per unit
- Applies traffic-light rules (green/yellow/red by distance)
- Exports 15 agency reports + 1 master report
- Loads 18,133 trips into SQLite

**Dashboard (Streamlit):**
- 5 KPI cards (total cost, off-hours cost, liters, cost/unit, cost/trip)
- 4 interactive charts (cost by agency, off-hours donut, idle heatmap, daily trend)
- 3 filters (agency, month, schedule)
- AI chat sidebar powered by Groq (Llama 3.3 70B) -- ask questions in Spanish, get SQL-backed answers

## Business rules

| Metric | Value |
|--------|-------|
| Fuel efficiency | 17.23 km/L (fleet average) |
| Gas price | $23.24 MXN/L (Mar 2026) |
| Green | < 3,000 km/month |
| Yellow | 3,000 - 6,000 km/month |
| Red | > 6,000 km/month |

## Data

Real GPS trip data from fleet vehicles:

- `data_gps/dic_2021/` -- 7 files (Aguascalientes, Celaya, Queretaro, San Juan, Silao, SLP, Zacatecas)
- `data_gps/ene_2022/` -- 8 files (same cities + Toluca)

## Tech stack

| Tool | Purpose |
|------|---------|
| Python 3.12 | Core language |
| pandas | Data cleaning, grouping, aggregation |
| openpyxl | Excel reading and formatting |
| SQLite | Analytical database |
| Streamlit | Dashboard UI |
| Plotly | Interactive charts |
| Groq (Llama 3.3 70B) | AI chat for natural language queries |

## Project structure

```text
gps-fleet-analytics/
├── main.py                      # ETL orchestrator
├── app.py                       # Dashboard orchestrator (Streamlit)
├── eda.ipynb                    # Exploratory data analysis
├── requirements.txt
├── .gitignore
├── docs/
│   ├── BUSINESS_RULES.md        # Fuel, cost, and threshold rules
│   ├── ARCHITECTURE.md          # System architecture and module map
│   └── screenshots/             # Dashboard screenshots for portfolio
├── src/
│   ├── etl/
│   │   ├── extract.py           # Read raw Excel, parse dates/times
│   │   ├── transform.py         # Summaries, traffic light, renumber units
│   │   ├── load.py              # Export to Excel
│   │   └── database.py          # SQLite connection and loading
│   └── dashboard/
│       ├── charts.py            # Plotly chart factory
│       ├── chat.py              # Groq AI integration
│       └── queries.py           # SQL queries and filter logic
└── data_gps/
    ├── dic_2021/                # 7 raw Excel files (Dec 2021)
    ├── ene_2022/                # 8 raw Excel files (Jan 2022)
    ├── output/                  # Generated reports (gitignored)
    └── reference/               # Legacy notebooks (gitignored)
```

## Usage

```bash
# Run ETL pipeline (generates reports + fleet.db)
python main.py

# Run dashboard
streamlit run app.py
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env with your Groq API key (for AI chat)
echo "GROQ_API_KEY=your_key_here" > .env

# Run ETL first, then dashboard
python main.py
streamlit run app.py
```

## License

Portfolio project for demonstration purposes.

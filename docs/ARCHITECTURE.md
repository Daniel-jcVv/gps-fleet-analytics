# Arquitectura — GPS Fleet Analytics

## Diagrama del pipeline

```
                         RAW DATA
                    (15 archivos Excel)
                           |
                           v
    +----------------------------------------------+
    |                  ETL PIPELINE                 |
    |                  (main.py)                    |
    |                                              |
    |   extract.py -----> transform.py -----> load.py
    |   - Lee Excel       - renumber_units()   - Excel report
    |   - Parsea fechas   - build_summary()    - Hoja "data"
    |   - Flag off_hours  - traffic_light()    |
    |   - travel/idle min                      |
    |                                          v
    |                                    database.py
    |                                    - SQLite (fleet.db)
    |                                    - 18,133 trips
    +----------------------------------------------+
                           |
                           v
                      fleet.db (SQLite)
                           |
                           v
    +----------------------------------------------+
    |               DASHBOARD                       |
    |               (app.py + Streamlit)             |
    |                                              |
    |   queries.py -----> charts.py                |
    |   - SQL queries      - Plotly charts          |
    |   - build_where()    - bar, donut, heatmap    |
    |   - KPIs             - area (tendencia)       |
    |                                              |
    |   chat.py                                    |
    |   - Groq API (Llama 3.3 70B)                 |
    |   - Natural language -> SQL -> DataFrame      |
    +----------------------------------------------+
                           |
                           v
                    Streamlit UI
              (filtros + graficas + chat)
```

## Flujo de datos

```
Excel (A:G cols) --> pandas DataFrame --> SQLite --> SQL queries --> Plotly/Streamlit
```

## Modulos

| Modulo | Ubicacion | Responsabilidad |
| --- | --- | --- |
| main.py | raiz | Orquestador ETL |
| app.py | raiz | Orquestador Dashboard |
| extract.py | src/etl/ | Lectura raw, constantes, parseo fechas |
| transform.py | src/etl/ | Resumen, semaforo, renumeracion |
| load.py | src/etl/ | Exportar a Excel |
| database.py | src/etl/ | Conexion y carga SQLite |
| charts.py | src/dashboard/ | Fabrica de graficas Plotly |
| chat.py | src/dashboard/ | Integracion con Groq AI |
| queries.py | src/dashboard/ | Queries SQL y logica de filtros |

## Dependencias entre modulos

```
main.py
  └── src/etl/extract.py (constantes, process_file)
  └── src/etl/transform.py (renumber_units)
  └── src/etl/load.py (export_report)
  └── src/etl/database.py (create_connection, load_trips)

app.py
  └── src/etl/database.py (create_connection)
  └── src/dashboard/charts.py (make_chart)
  └── src/dashboard/chat.py (ask_groq)
  └── src/dashboard/queries.py (build_where, get_*)

src/dashboard/queries.py
  └── src/etl/extract.py (FUEL_EFFICIENCY, FUEL_PRICE)
```

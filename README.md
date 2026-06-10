# GTFS Query Portal — Setup and Run Guide

This project is a **GTFS-based public transportation query portal** built with:
- **FastAPI** for the backend
- **PostgreSQL** as the database
- **PostGIS** for spatial queries
- **pgRouting** for route calculation
- **MobilityDB** for trajectory and spatio-temporal queries
- **Leaflet + OpenStreetMap** for the frontend map

This guide explains how to prepare and run the project from scratch on another PC.

---

## 1. What is included

The project contains:
- GTFS CSV files inside the `data/` folder
- SQL helpers for creating tables, indexes, and extensions
- FastAPI backend routers
- frontend files in:
  - `template/index.html`
  - `static/app.js`
  - `static/style.css`

When the backend starts, it attempts to:
1. connect to PostgreSQL
2. load the GTFS CSV data into the database
3. expose API endpoints
4. open the web interface at `/` or `/map`

---

## 2. Prerequisites

Install these first:

### Software
- **Python 3.10**
- **PostgreSQL**
- **PostGIS** extension
- **pgRouting** extension
- **MobilityDB** extension
- **Git** (optional, only if cloning the repository)

### Tested Python packages
The project currently uses:
- `fastapi==0.104.1`
- `uvicorn==0.24.0`
- `psycopg2-binary==2.9.9`
- `pydantic==2.5.0`
- `python-dotenv==1.0.0`
- `pandas` *(required by `load_data.py`)*

> Note: `pandas` is required even though it is not listed in the current `requirements.txt`, because `load_data.py` imports it.

---

## 3. Project folder structure

Important folders/files:

```text
project_root/
│
├── data/                  # GTFS CSV files
├── sql/                   # SQL scripts
├── static/                # frontend JS/CSS
├── template/              # frontend HTML
├── main.py                # FastAPI entry point
├── load_data.py           # imports CSV data into PostgreSQL
├── database_Creation.py   # DB connection helpers
├── requirements.txt       # Python dependencies
└── .env                   # local configuration
```

---

## 4. Database preparation

### 4.1 Create a PostgreSQL database
Create a new database, for example:

```sql
CREATE DATABASE gtfs_portals;
```

### 4.2 Enable required extensions
Connect to that database and run:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;
CREATE EXTENSION IF NOT EXISTS mobilitydb;
```

### 4.3 Create the GTFS tables
Run the provided SQL scripts in this order:

1. `sql/extensions.sql`
2. `sql/create_tables.sql`
3. `sql/add_geomtery.sql`
4. `sql/indexes.sql`

If preferred, these can also be run manually from pgAdmin.

---

## 5. Environment configuration

Create a `.env` file in the project root.

Use this format:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gtfs_portals
DB_USER=postgres
DB_PASSWORD=your_password_here

API_PORT=8000
API_HOST=127.0.0.1
```

### Important note
The current code reads **`DB_NAME`**, not `DB_DATABASE`.
So if `.env.example` contains `DB_DATABASE`, replace it with:

```env
DB_NAME=gtfs_portals
```

---

## 6. Python environment setup

Open a terminal in the project root.

### 6.1 Create a virtual environment

```bash
py -3.10 -m venv venv
```

### 6.2 Activate the virtual environment

#### PowerShell
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

#### Command Prompt
```cmd
venv\Scripts\activate.bat
```

### 6.3 Install Python packages

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install pandas
```

---

## 7. Running the project

From the project root, run:

```bash
uvicorn main:app --reload
```

If startup succeeds, the terminal should show that:
- the database connection is successful
- GTFS data is being loaded
- the FastAPI server is running

---

## 8. Open the application

After the server starts, open one of these URLs in the browser:

### Main interface
```text
http://127.0.0.1:8000/
```

or

```text
http://127.0.0.1:8000/map
```

### Swagger API docs
```text
http://127.0.0.1:8000/docs
```

---

## 9. What should work

The project should expose these main backend groups:
- `/gtfs`
- `/stops`
- `/realtime`
- `/routing`
- `/analysis`
- `/mobility`

The frontend should allow testing of:
- stop queries
- route display
- shortest path (Dijkstra / A*)
- spatial window query
- nearest-neighbor style queries
- MobilityDB trajectory visualization

---

## 10. Quick test checklist

After opening the app:

### Browser tests
- load a route from the **Explore** tab
- find nearest stops from the **Spatial Tools** tab
- draw a window query on the map
- run Dijkstra or A* from the **Routing** tab
- show all trajectories from the **Mobility** tab

### API tests
Open `/docs` and test:
- `GET /stops/{stop_id}`
- `GET /stops/nearest`
- `GET /stops/inarea`
- `GET /analysis/dijkstra`
- `GET /analysis/astar`
- `GET /mobility/trajectories`
- `GET /mobility/at-time`
- `GET /mobility/in-window`

---

## 11. Known issues / troubleshooting

### 1. `ModuleNotFoundError: No module named 'pandas'`
Install pandas:

```bash
pip install pandas
```

### 2. Database authentication failed
Check `.env`:
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

### 3. Frontend opens but buttons do not return results
Check that:
- the backend is running
- `/docs` opens correctly
- the frontend files in use are:
  - `template/index.html`
  - `static/app.js`

### 4. Map container already initialized
Make sure `initMap()` is only called once in `static/app.js`.

### 5. MobilityDB functions fail
Check that the extension is installed in the same database:

```sql
CREATE EXTENSION IF NOT EXISTS mobilitydb;
```

---

## 12. Notes for evaluation

This project is intended to demonstrate:
- GTFS import into PostgreSQL
- spatial SQL with PostGIS
- shortest-path computation with pgRouting
- interactive map-based queries in the browser
- spatio-temporal trajectory queries with MobilityDB

---

## 13. Recommended way to share the project

To run the project on another PC, share:
- the full project folder
- the `data/` folder with CSV files
- this README
- a sample `.env` template (without private password)

If the evaluator does not already have PostgreSQL extensions installed, those must be installed first before the backend can run correctly.


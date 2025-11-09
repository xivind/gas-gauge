# Gas Gauge Design Document

**Date:** 2025-11-09
**Purpose:** Web application to track remaining gas in canisters for camp stoves

## Overview

Gas Gauge is a single-user web application that replaces spreadsheet-based tracking of camping gas canisters. Users weigh canisters after trips, record the weights with comments, and view remaining gas percentages to choose appropriate canisters for upcoming trips.

## User Workflow

1. **After a trip:** User weighs canister and records weight + optional comment about the trip
2. **Before a trip:** User views dashboard showing all active canisters with remaining percentages, selects appropriate canister based on trip length
3. **Canister lifecycle:** When canister depleted, mark as depleted (moves to archive but retains all history)

## Data Model

### Database Tables (Peewee ORM with SQLite)

**CanisterType** - Predefined canister specifications
- `id`: Primary key
- `name`: String (e.g., "Coleman 240g")
- `full_weight`: Integer (grams, e.g., 361)
- `empty_weight`: Integer (grams, e.g., 122)
- `gas_capacity`: Computed property (full_weight - empty_weight)

**Canister** - Individual physical canisters owned by user
- `id`: Primary key
- `label`: String (e.g., "Gas Canister A")
- `canister_type_id`: Foreign key to CanisterType
- `status`: Enum ("active", "depleted")
- `created_at`: Timestamp

**Weighing** - Individual weight recordings
- `id`: Primary key
- `canister_id`: Foreign key to Canister
- `weight`: Integer (grams)
- `comment`: Text (nullable)
- `recorded_at`: Timestamp
- Computed properties:
  - `remaining_gas`: weight - canister.type.empty_weight
  - `remaining_percentage`: (remaining_gas / canister.type.gas_capacity) * 100
  - `consumption_percentage`: 100 - remaining_percentage

## UI Structure & Pages

### Dashboard Page (`/`)
- Card grid showing all **active** canisters
- Each card displays:
  - Canister label
  - Canister type name
  - Latest weighing percentage (large, prominent)
  - Visual indicator (color-coded: green >50%, yellow 25-50%, red <25%)
  - Last weighed date
- Action buttons:
  - "Add New Canister"
  - "View Depleted Archive"
- Click any card → navigates to canister detail page
- Bar chart showing all active canisters side-by-side with remaining percentages

### Canister Detail Page (`/canister/{id}`)
- Header section:
  - Canister label and type
  - Current percentage (large)
  - "Add Weighing" button
  - "Mark as Depleted" button (if active)
  - "Reactivate" button (if depleted)
- History table:
  - Columns: Date, Weight (g), Remaining Gas (g), Remaining (%), Consumption (%), Comment
  - Sorted newest first
  - Shows full history for this canister
- Visualizations:
  - Line chart: Gas remaining over time (shows consumption trend)
  - Optional bar chart: Consumption per weighing with hover showing comments
- Back to dashboard link

### Archive Page (`/archive`)
- Card grid showing only **depleted** canisters
- Cards show final weighing data
- Click to view full history (same detail page structure)
- Back to dashboard link

### Admin Page (`/admin/types`)
- Table listing all canister types
- Columns: Name, Full Weight (g), Empty Weight (g), Gas Capacity (g), Actions
- "Add New Type" button opens form
- Edit/Delete actions for custom types
- Seed types (Coleman 240g, 450g, etc.) marked as built-in and non-deletable

## Technical Architecture

### Backend Stack
- **Framework:** FastAPI
- **ORM:** Peewee
- **Database:** SQLite (file: `data/gas_gauge.db`)
- **Templates:** Jinja2
- **Server:** Uvicorn

### Backend Structure
```
routers/
├── canisters.py      # CRUD for canisters
├── weighings.py      # Add/view weighings
└── canister_types.py # Manage types

main.py               # App initialization, route registration
models.py             # Peewee ORM models
database.py           # SQLite connection, initialization
schemas.py            # Pydantic request/response validation
seed_data.py          # Populate common canister types
```

### Frontend Stack
- **Templates:** Jinja2
- **CSS Framework:** Bootstrap
- **JavaScript:** Vanilla JS
- **Dropdown Library:** TomSelect
- **Charts:** Chart.js

### Frontend Structure
```
templates/
├── base.html           # Base layout with Bootstrap
├── dashboard.html      # Active canisters grid
├── archive.html        # Depleted canisters
├── canister_detail.html # Individual canister history
└── admin/
    └── types.html      # Canister type management

static/
├── css/
│   └── custom.css      # Color-coding, custom styles
└── js/
    ├── app.js          # Form handling, interactions
    └── charts.js       # Chart.js rendering functions
```

### Data Flow Example (Adding a Weighing)
1. User clicks "Add Weighing" on detail page
2. Modal/form appears with weight input and comment field
3. JS submits form to POST `/api/weighings`
4. FastAPI validates data via Pydantic schema
5. Creates Weighing record via Peewee ORM
6. Returns success response
7. Page refreshes or table updates dynamically
8. Computed properties (percentage, consumption) calculated from model methods

## Visualizations (Chart.js)

### Dashboard
- Bar chart: All active canisters with remaining percentages
- Color-coded bars (green/yellow/red)
- Quick visual comparison

### Canister Detail
- Line chart: Gas remaining over time (trend analysis)
- Bar chart: Consumption per weighing (hover shows trip comments)

## Deployment

### Docker Setup
- Single `Dockerfile` with Python slim base
- No docker-compose (plain Docker commands)
- Volume mount for database persistence: `-v $(pwd)/data:/app/data`
- Port mapping: `-p 8000:8000`

### Commands
```bash
# Build
docker build -t gas-gauge .

# Run
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --name gas-gauge gas-gauge

# View logs
docker logs -f gas-gauge

# Stop/Start
docker stop gas-gauge
docker start gas-gauge

# Remove
docker rm gas-gauge
```

### Logging
- Python logging to stdout/stderr
- FastAPI access logs to console
- Application logs: timestamp, level, module, message
- Logged events:
  - App startup and database initialization
  - API requests (method, path, status)
  - Weighing additions and canister updates
  - Errors and warnings
- All logs visible via `docker logs -f gas-gauge`

## Database Initialization
- On first run, create tables automatically
- Seed common canister types (Coleman 240g, 450g, etc.)
- Database file persisted in `data/` directory via Docker volume

## User Model
- Single-user per instance (no authentication)
- Each person runs their own Docker container
- Simple deployment, no user management complexity
- Easy to share code for others to clone and run

## Sharing & Distribution
- GitHub repository with MIT license
- README includes:
  - Quick start with Docker commands
  - How to view logs
  - Database backup instructions (copy `./data` folder)
  - Screenshot of dashboard
  - How to add custom canister types
- Users clone repo and run with Docker

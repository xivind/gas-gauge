# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gas Gauge is a web application to track remaining gas in canisters for camp stoves. Users weigh canisters after trips, record weights with comments, and view remaining gas percentages to choose appropriate canisters for upcoming trips.

## Technology Stack

- **Backend:** FastAPI, Uvicorn, Peewee ORM, SQLite
- **Frontend:** Jinja2 templates, Bootstrap 5, Chart.js, TomSelect, Vanilla JavaScript
- **Deployment:** Docker (no docker-compose)
- **Testing:** pytest

## Development Commands

### Deployment

**Using deploy.sh script (recommended):**
```bash
./deploy.sh
```

The deploy.sh script handles complete deployment lifecycle:
- Stops and removes existing container
- Removes old image
- Builds fresh image
- Creates container with persistent data volume
- Database stored in `~/code/container_data` (persists across rebuilds)

**Manual Docker commands:**
```bash
# Build
docker build -t gas-gauge .

# Run (with data persistence)
mkdir -p ~/code/container_data
docker run -d \
  --name=gas-gauge \
  -e TZ=Europe/Stockholm \
  -v ~/code/container_data:/app/data \
  --restart unless-stopped \
  -p 8000:8000 \
  gas-gauge

# View logs
docker logs -f gas-gauge
# or
docker container logs -f gas-gauge

# Stop/Start
docker stop gas-gauge
docker start gas-gauge
```

### Running the App

**Without Docker:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn main:app --reload --log-config uvicorn_log_config.ini

# Run for production
uvicorn main:app --host 0.0.0.0 --port 8000 --log-config uvicorn_log_config.ini
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Architecture

### Database Models

Three main models with computed properties:

1. **CanisterType**: Predefined specifications (Coleman 240g, etc.)
   - Stores: name, full_weight, empty_weight
   - Computes: gas_capacity

2. **Canister**: Individual physical canisters
   - Stores: id (UUID string), label (editable name), type reference, status (active/depleted)
   - Has many: weighings
   - ID format: GC-{uuid[:6]}{timestamp[-4:]} (e.g., GC-a3f8e52468)

3. **Weighing**: Weight recordings over time
   - Stores: weight, comment, timestamp
   - Computes: remaining_gas, remaining_percentage, consumption_percentage

### Router Structure

- `routers/canister_types.py`: API for managing canister types
- `routers/canisters.py`: API for canister CRUD
- `routers/weighings.py`: API for recording weighings
- `routers/views.py`: HTML views (dashboard, detail, admin) with deletion routes

### Frontend Organization

- `templates/base.html`: Base template with Bootstrap, Chart.js, TomSelect, navbar with logo
- `templates/dashboard.html`: All canisters with "Show Depleted" toggle and overview chart
- `templates/canister_detail.html`: Individual canister with history, charts, and deletion
- `templates/admin/types.html`: Manage canister types
- `static/css/custom.css`: Color-coded status indicators and navbar styling
- `static/js/charts.js`: Chart.js helper functions
- `static/js/app.js`: Form handling and utilities
- `static/gas_gauge.png`: Transparent logo image (1024x1024)
- `static/favicon.ico`: Browser favicon

### Color Coding Logic

Status classes based on remaining percentage and measurement state:
- **high** (green #28a745): > 50%
- **medium** (yellow #ffc107): 25-50%
- **low** (red #dc3545): < 25%
- **none** (gray #6c757d): No measurements recorded yet
- **depleted** (purple #8b5cf6): Marked as depleted/empty

Implemented in `routers/views.py::get_status_class()` and styled in `static/css/custom.css`

### Logging

Unified logging configuration for both FastAPI/uvicorn and application logs:
- Format: `%(asctime)s - %(levelname)s - %(message)s`
- Date format: `%Y-%m-%d %H:%M:%S` (ISO 8601 / YYYY-MM-DD format)
- Configured in `logger.py` and `uvicorn_log_config.ini`
- All uvicorn loggers (root, uvicorn, uvicorn.access, uvicorn.error) use same format
- All logs output to stdout for Docker visibility
- View with: `docker logs -f gas-gauge`
- Logs: startup, requests, weighing additions, errors

**Important:** Always run uvicorn with `--log-config uvicorn_log_config.ini` for consistent formatting.

## Key Features

### Show Depleted Toggle

Dashboard displays all canisters with a "Show Depleted" toggle (off by default):
- Toggle implemented as Bootstrap form switch below main heading
- JavaScript hides depleted canisters by default
- Depleted canisters always sort to the end when visible
- No page reload required - pure client-side show/hide
- Chart data excludes depleted canisters

**Implementation:**
- `templates/dashboard.html`: Form switch and JavaScript toggle logic
- `routers/views.py::dashboard()`: Fetches all canisters, marks depleted status
- Sorting: `canister_data.sort(key=lambda x: (x["is_depleted"], x["canister"].label))`

### Deletion Functionality

**Delete Canisters:**
- Available on canister detail page
- Cascade delete: removes all associated weighing records first
- Confirmation dialog warns about permanent data loss
- Route: `POST /canister/{canister_id}/delete`
- Redirects to dashboard after deletion

**Delete Weighing Records:**
- Each weighing row has individual delete button
- Confirmation dialog for each deletion
- Route: `POST /weighing/{weighing_id}/delete`
- Redirects back to canister detail page

**Implementation:**
- `routers/views.py`: `delete_canister()` and `delete_weighing()` routes
- `templates/canister_detail.html`: Delete buttons with onclick confirmations

### UUID-Based Primary Keys

Canisters use UUID-based strings as primary keys instead of auto-incrementing integers:
- **Format:** `GC-{uuid[:6]}{timestamp[-4:]}`
- **Example:** `GC-a3f8e52468`
- **Characteristics:**
  - Combines UUID randomness with timestamp uniqueness
  - 13 characters total (3 prefix + 10 random/timestamp)
  - Used as immutable primary key in database

**Separate Label Field:**
- User-editable friendly name (1-64 characters, required)
- Can be non-unique (multiple canisters can have same label)
- Used for display and searching
- Editable via canister detail page

**Implementation:**
- `utils.py::generate_canister_id()`: ID generation function
- `routers/canisters.py::create_canister()`: Generates ID before database insert
- `routers/views.py::dashboard()`: Passes suggested_label to template
- `routers/views.py::update_canister_label()`: POST route for label updates
- `templates/dashboard.html`: Form with label field (suggested value)
- `templates/canister_detail.html`: Label edit form

### UI/UX Improvements

**Navbar:**
- Dark theme with large transparent logo (70px height)
- Vertically centered logo and navigation links
- Increased font size for better readability (1.1rem)
- Logo and favicon use transparent PNG and ICO files

**Consistency:**
- All "Back to Dashboard" buttons use same styling (btn btn-secondary)
- Color-coded status indicators throughout (green/yellow/red)
- Standardized form layouts and button positions

## Database Management

### Location
- Development (local): `./data/gas_gauge.db`
- Production (Docker): `~/code/container_data/gas_gauge.db`
  - Persisted via volume mount `-v ~/code/container_data:/app/data`
  - Survives container rebuilds and updates

### Initialization
- Tables created automatically on first run
- Seed data (Coleman types) populated by `seed_data.py`

### Backup
```bash
# Production database
cp -r ~/code/container_data ~/code/container_data-backup-$(date +%Y%m%d)

# Development database
cp -r ./data ./data-backup-$(date +%Y%m%d)
```

### Database Recreation (UUID Migration)

To recreate database with UUID-based IDs:

```bash
# Backup existing database first
cp -r ./data ./data-backup-$(date +%Y%m%d)

# Recreate tables with new schema
python recreate_db.py
```

This will:
1. Drop all existing tables (Weighing, Canister, CanisterType)
2. Create tables with new schema (UUID primary keys)
3. Seed canister types (Coleman 240g, Coleman 450g)
4. Result: Fresh database with no data

## Key Design Decisions

1. **Single-user per instance**: No authentication, simpler deployment
2. **SQLite**: Lightweight, file-based, easy backup
3. **Computed properties**: Percentages calculated on-the-fly from model methods
4. **Depleted status + optional deletion**: Depleted status preserves history by default; hard delete available when needed with cascade to weighings
5. **Vanilla JS**: No build step, keep frontend simple; client-side toggle for show/hide
6. **TomSelect for dropdowns**: Better UX than plain select elements
7. **Chart.js**: Visualize trends without heavy dependencies
8. **UUID-based IDs**: Robust unique identifiers combining UUID + timestamp for canister labels
9. **Unified logging**: Consistent format across uvicorn and application logs for easier debugging
10. **Date format consistency**: All dates use ISO 8601 format (YYYY-MM-DD) across GUI, database, logs, and APIs for consistency and internationalization

## Worktree Configuration

Worktrees should be created in `.worktrees/` (already in .gitignore).

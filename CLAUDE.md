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

### Running the App

**With Docker (recommended):**
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
```

**Without Docker:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn main:app --reload

# Run for production
uvicorn main:app --host 0.0.0.0 --port 8000
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
   - Stores: label, type reference, status (active/depleted)
   - Has many: weighings

3. **Weighing**: Weight recordings over time
   - Stores: weight, comment, timestamp
   - Computes: remaining_gas, remaining_percentage, consumption_percentage

### Router Structure

- `routers/canister_types.py`: API for managing canister types
- `routers/canisters.py`: API for canister CRUD
- `routers/weighings.py`: API for recording weighings
- `routers/views.py`: HTML views (dashboard, detail, archive, admin)

### Frontend Organization

- `templates/base.html`: Base template with Bootstrap, Chart.js, TomSelect
- `templates/dashboard.html`: Active canisters with overview chart
- `templates/canister_detail.html`: Individual canister with history and charts
- `templates/archive.html`: Depleted canisters
- `templates/admin/types.html`: Manage canister types
- `static/css/custom.css`: Color-coded status indicators
- `static/js/charts.js`: Chart.js helper functions
- `static/js/app.js`: Form handling and utilities

### Color Coding Logic

Status classes based on remaining percentage:
- **high** (green): > 50%
- **medium** (yellow): 25-50%
- **low** (red): < 25%

Implemented in `routers/views.py::get_status_class()`

### Logging

Unified logging configuration for both FastAPI/uvicorn and application logs:
- Format: `%(asctime)s - %(levelname)s - %(message)s`
- Date format: `%d-%b-%y %H:%M:%S`
- Configured in `logger.py` and `uvicorn_log_config.ini`
- All logs output to stdout for Docker visibility
- View with: `docker logs -f gas-gauge`
- Logs: startup, requests, weighing additions, errors

## Database Management

### Location
- Development: `./data/gas_gauge.db`
- Docker: Persisted via volume mount `-v $(pwd)/data:/app/data`

### Initialization
- Tables created automatically on first run
- Seed data (Coleman types) populated by `seed_data.py`

### Backup
```bash
cp -r ./data ./data-backup-$(date +%Y%m%d)
```

## Key Design Decisions

1. **Single-user per instance**: No authentication, simpler deployment
2. **SQLite**: Lightweight, file-based, easy backup
3. **Computed properties**: Percentages calculated on-the-fly from model methods
4. **No soft deletes**: Depleted status preserves history without deletion
5. **Vanilla JS**: No build step, keep frontend simple
6. **TomSelect for dropdowns**: Better UX than plain select elements
7. **Chart.js**: Visualize trends without heavy dependencies

## Worktree Configuration

Worktrees should be created in `.worktrees/` (already in .gitignore).

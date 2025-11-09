# Gas Gauge

A web application to track remaining gas in canisters for camp stoves.

![Dashboard Screenshot](docs/screenshot.png)

## Features

- **Dashboard**: View all active canisters with remaining gas percentages
- **Weighing History**: Track multiple weighings per canister over time
- **Visual Analytics**: Charts showing gas consumption trends
- **Archive**: Keep history of depleted canisters
- **Custom Types**: Add your own canister types
- **Color-coded Status**: Quick visual identification of canister levels
  - Green: >50% remaining
  - Yellow: 25-50% remaining
  - Red: <25% remaining

## Quick Start

### Using Docker

1. **Build the image:**
   ```bash
   docker build -t gas-gauge .
   ```

2. **Run the container:**
   ```bash
   docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --name gas-gauge gas-gauge
   ```

3. **Open your browser:**
   Navigate to `http://localhost:8000`

### View Logs

```bash
docker logs -f gas-gauge
```

### Stop/Start

```bash
docker stop gas-gauge
docker start gas-gauge
```

### Remove Container

```bash
docker stop gas-gauge
docker rm gas-gauge
```

## Database Backup

Your data is stored in `./data/gas_gauge.db`. To backup:

```bash
cp -r ./data ./data-backup-$(date +%Y%m%d)
```

## Development

### Local Setup (without Docker)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   uvicorn main:app --reload
   ```

3. **Run tests:**
   ```bash
   pytest
   ```

### Project Structure

```
gas-gauge/
├── main.py              # FastAPI app initialization
├── models.py            # Database models
├── database.py          # Database connection
├── schemas.py           # Pydantic schemas
├── seed_data.py         # Seed predefined canister types
├── logger.py            # Logging configuration
├── routers/             # API and view routes
├── templates/           # Jinja2 templates
├── static/              # CSS and JavaScript
├── tests/               # Test suite
└── data/                # SQLite database (created at runtime)
```

## Usage Guide

### Adding a Canister

1. Click "Add New Canister" on the dashboard
2. Enter a label (e.g., "Gas Canister A")
3. Select canister type
4. Click "Add Canister"

### Recording a Weighing

1. Click on a canister card
2. Click "Add Weighing"
3. Enter weight in grams
4. Optionally add a comment about the trip
5. Click "Add Weighing"

### Marking as Depleted

1. Go to canister detail page
2. Click "Mark as Depleted"
3. Canister moves to archive but retains all history

### Adding Custom Canister Types

1. Navigate to "Canister Types" in the menu
2. Click "Add New Type"
3. Enter name, full weight, and empty weight
4. Gas capacity is calculated automatically

## Tech Stack

- **Backend:** FastAPI, Peewee ORM, SQLite
- **Frontend:** Bootstrap 5, Chart.js, TomSelect, Vanilla JavaScript
- **Templates:** Jinja2
- **Deployment:** Docker

## License

MIT License - feel free to clone and run your own instance!

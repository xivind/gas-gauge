from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import init_db
from seed_data import seed_canister_types
from logger import setup_logging
from routers import canister_types, canisters, weighings, views
import logging

# Setup logging
logger = setup_logging()

# Initialize app
app = FastAPI(title="Gas Gauge")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize database
logger.info("Initializing database...")
init_db()
seed_canister_types()
logger.info("Database initialized")

# Include routers
app.include_router(canister_types.router)
app.include_router(canisters.router)
app.include_router(weighings.router)
app.include_router(views.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

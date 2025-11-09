from fastapi import FastAPI
from database import init_db
from logger import setup_logging
from routers import canister_types

# Setup logging
setup_logging()

# Initialize app
app = FastAPI(title="Gas Gauge")

# Initialize database
init_db()

# Include routers
app.include_router(canister_types.router)

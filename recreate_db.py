#!/usr/bin/env python3
"""Drops, creates, and seeds the database.

This script is idempotent and can be run safely to reset the database to a clean state.
It uses the centralized logging configuration.
"""

import logging
from database import db
from models import Canister, CanisterType, Weighing
from seed_data import seed_canister_types
from logger import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

def recreate_database():
    """Drops all tables, recreates them, and seeds with initial data."""
    logger.info("Starting database recreation process...")
    
    try:
        db.connect()
        logger.info("Database connection successful.")

        logger.warning("Dropping all tables: Weighing, Canister, CanisterType")
        db.drop_tables([Weighing, Canister, CanisterType])
        logger.info("Tables dropped successfully.")

        logger.info("Creating all tables...")
        db.create_tables([CanisterType, Canister, Weighing])
        logger.info("Tables created successfully.")

        # Seed canister types using the refactored seed function
        seed_canister_types()

        logger.info("Database recreation and seeding process completed successfully!")

    except Exception as e:
        logger.critical(f"An error occurred during database recreation: {e}", exc_info=True)
    finally:
        if not db.is_closed():
            db.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    # This confirmation provides a safeguard against accidental execution.
    confirm = input("Are you sure you want to completely recreate the database? All data will be lost. (yes/no): ")
    if confirm.lower() == 'yes':
        recreate_database()
    else:
        logger.info("Database recreation aborted by user.")

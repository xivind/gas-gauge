#!/usr/bin/env python3
"""Drop and recreate database tables for UUID migration"""

import os
from database import db, init_db
from models import CanisterType, Canister, Weighing
from seed_data import seed_canister_types
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_database():
    """Drop all tables and recreate with new schema"""
    logger.info("Connecting to database...")
    db.connect()

    # Drop existing tables
    logger.info("Dropping existing tables...")
    db.drop_tables([Weighing, Canister, CanisterType], safe=True)

    # Create tables with new schema
    logger.info("Creating tables with new schema...")
    db.create_tables([CanisterType, Canister, Weighing])

    # Seed canister types
    logger.info("Seeding canister types...")
    seed_canister_types()

    logger.info("Database recreation complete!")
    db.close()

if __name__ == "__main__":
    recreate_database()

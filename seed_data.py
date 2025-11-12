import logging
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

PREDEFINED_TYPES = [
    {"name": "Coleman 240g", "full_weight": 361, "empty_weight": 122},
]

def seed_canister_types():
    """Seed database with predefined canister types using the database manager."""
    logger.info("Seeding predefined canister types...")
    db_manager = DatabaseManager()

    for type_data in PREDEFINED_TYPES:
        success, message = db_manager.write_canister_type(type_data)
        logger.info(message)

    logger.info("Canister type seeding complete.")

import logging
import database_manager as db_manager

logger = logging.getLogger(__name__)

PREDEFINED_TYPES = [
    {"name": "Coleman 240g", "full_weight": 361, "empty_weight": 122},
    {"name": "Coleman 450g", "full_weight": 668, "empty_weight": 218}
]

def seed_canister_types():
    """Seed database with predefined canister types using the database manager."""
    logger.info("Seeding predefined canister types...")
    for type_data in PREDEFINED_TYPES:
        db_manager.create_canister_type(
            name=type_data["name"],
            full_weight=type_data["full_weight"],
            empty_weight=type_data["empty_weight"]
        )
    logger.info("Canister type seeding complete.")

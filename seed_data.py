from models import CanisterType
import logging

logger = logging.getLogger(__name__)

PREDEFINED_TYPES = [
    {"name": "Coleman 240g", "full_weight": 361, "empty_weight": 122}
]

def seed_canister_types():
    """Seed database with predefined canister types"""
    for type_data in PREDEFINED_TYPES:
        canister_type, created = CanisterType.get_or_create(
            name=type_data["name"],
            defaults={
                "full_weight": type_data["full_weight"],
                "empty_weight": type_data["empty_weight"]
            }
        )
        if created:
            logger.info(f"Created canister type: {canister_type.name}")
        else:
            logger.debug(f"Canister type already exists: {canister_type.name}")

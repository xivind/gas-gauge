import logging
from datetime import datetime
from models import Canister, CanisterType, Weighing
from utils import generate_canister_id
from peewee import fn

logger = logging.getLogger(__name__)

#==============================================================================
# Canister Type Operations
#==============================================================================

def create_canister_type(name: str, full_weight: int, empty_weight: int) -> CanisterType:
    """Create a new canister type."""
    try:
        canister_type, created = CanisterType.get_or_create(
            name=name,
            defaults={'full_weight': full_weight, 'empty_weight': empty_weight}
        )
        if created:
            logger.info(f"Created canister type '{name}' with ID {canister_type.id}")
        else:
            logger.info(f"Canister type '{name}' already exists.")
        return canister_type
    except Exception as e:
        logger.error(f"Error creating canister type '{name}': {e}")
        raise

def get_all_canister_types() -> list[CanisterType]:
    """Get all canister types."""
    return list(CanisterType.select())

def delete_canister_type(type_id: int):
    """Delete a canister type."""
    try:
        canister_type = CanisterType.get_by_id(type_id)
        # Prevent deletion of built-in types
        if canister_type.name not in ['Coleman 240g', 'Coleman 450g']:
            canister_type.delete_instance()
            logger.info(f"Deleted canister type ID {type_id}")
    except CanisterType.DoesNotExist:
        logger.warning(f"Attempted to delete non-existent canister type ID {type_id}")
    except Exception as e:
        logger.error(f"Error deleting canister type ID {type_id}: {e}")
        raise

#==============================================================================
# Canister Operations
#==============================================================================

def create_canister(label: str, canister_type_id: int) -> Canister:
    """Create a new canister."""
    try:
        canister_id = generate_canister_id()
        canister = Canister.create(
            id=canister_id,
            label=label,
            canister_type_id=canister_type_id
        )
        logger.info(f"Created canister '{label}' with ID {canister.id}")
        return canister
    except Exception as e:
        logger.error(f"Error creating canister '{label}': {e}")
        raise

def get_canister_by_id(canister_id: str) -> Canister:
    """Get a single canister by its ID."""
    try:
        return Canister.get_by_id(canister_id)
    except Canister.DoesNotExist:
        logger.warning(f"Canister with ID {canister_id} not found.")
        return None

def get_all_canisters() -> list[Canister]:
    """Get all canisters."""
    return list(Canister.select())

def update_canister_label(canister_id: str, new_label: str):
    """Update a canister's label."""
    try:
        canister = Canister.get_by_id(canister_id)
        old_label = canister.label
        canister.label = new_label.strip()
        canister.save()
        logger.info(f"Updated canister {canister_id} label from '{old_label}' to '{new_label}'")
    except Canister.DoesNotExist:
        logger.warning(f"Attempted to update label on non-existent canister ID {canister_id}")
    except Exception as e:
        logger.error(f"Error updating canister label for ID {canister_id}: {e}")
        raise

def update_canister_status(canister_id: str, status: str):
    """Update a canister's status."""
    try:
        canister = Canister.get_by_id(canister_id)
        canister.status = status
        canister.save()
        logger.info(f"Updated canister {canister_id} status to '{status}'")
    except Canister.DoesNotExist:
        logger.warning(f"Attempted to update status on non-existent canister ID {canister_id}")
    except Exception as e:
        logger.error(f"Error updating canister status for ID {canister_id}: {e}")
        raise

def delete_canister(canister_id: str):
    """Delete a canister and its associated weighings."""
    try:
        canister = get_canister_by_id(canister_id)
        if not canister:
            return # Already logged in get_canister_by_id
        
        # Cascade delete
        Weighing.delete().where(Weighing.canister == canister).execute()
        canister.delete_instance()
        logger.info(f"Deleted canister {canister_id} and all its weighings.")
    except Exception as e:
        logger.error(f"Error deleting canister ID {canister_id}: {e}")
        raise

#==============================================================================
# Weighing Operations
#==============================================================================

def create_weighing(canister_id: str, weight: int, recorded_at: datetime, comment: str) -> Weighing:
    """Create a new weighing record, ensuring it is a new entry."""
    try:
        canister = get_canister_by_id(canister_id)
        if not canister:
            raise ValueError(f"Canister with ID {canister_id} not found.")

        # Create a new Weighing instance without saving it
        weighing = Weighing(
            canister=canister,
            weight=weight,
            recorded_at=recorded_at,
            comment=comment
        )
        # Save it with force_insert=True to guarantee a new row
        weighing.save(force_insert=True)
        
        logger.info(f"Created new weighing {weighing.id} for canister {canister_id} ({weight}g)")
        return weighing
    except Exception as e:
        logger.error(f"Error creating weighing for canister {canister_id}: {e}")
        raise

def get_weighings_by_canister(canister: Canister) -> list[Weighing]:
    """Get all weighings for a specific canister, ordered by date descending."""
    return list(Weighing.select().where(Weighing.canister == canister).order_by(Weighing.recorded_at.desc()))

def get_latest_weighing(canister: Canister) -> Weighing:
    """Get the latest weighing for a specific canister."""
    return Weighing.select().where(Weighing.canister == canister).order_by(Weighing.recorded_at.desc()).first()

def get_weighing_by_id(weighing_id: str) -> Weighing:
    """Get a single weighing by its ID."""
    try:
        return Weighing.get_by_id(weighing_id)
    except Weighing.DoesNotExist:
        logger.warning(f"Weighing with ID {weighing_id} not found.")
        return None

def delete_weighing(weighing_id: str):
    """Delete a single weighing record."""
    try:
        weighing = Weighing.get_by_id(weighing_id)
        canister_id = weighing.canister.id
        weighing.delete_instance()
        logger.info(f"Deleted weighing {weighing_id} for canister {canister_id}.")
    except Weighing.DoesNotExist:
        logger.warning(f"Attempted to delete non-existent weighing ID {weighing_id}")
    except Exception as e:
        logger.error(f"Error deleting weighing ID {weighing_id}: {e}")
        raise

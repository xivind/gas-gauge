"""
Database manager for Gas Gauge application.
Handles all database operations using Peewee ORM.
Includes database setup (merged from database.py).
"""

import os
import peewee
import logging
from peewee import SqliteDatabase
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Database setup (from old database.py)
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/gas_gauge.db")
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
database = SqliteDatabase(DATABASE_PATH)

class DatabaseManager:
    """Manages all database operations with transaction safety"""

    def __init__(self):
        self.database = database
        # Bind database to models
        from database_model import BaseModel, CanisterType, Canister, Weighing
        BaseModel._meta.database = self.database
        CanisterType._meta.database = self.database
        Canister._meta.database = self.database
        Weighing._meta.database = self.database

    def init_db(self):
        """Initialize database tables"""
        from database_model import CanisterType, Canister, Weighing
        self.database.connect()
        self.database.create_tables([CanisterType, Canister, Weighing], safe=True)
        self.database.close()
        logger.info("Database tables initialized")

    # ========== Canister Type Operations ==========

    def read_all_canister_types(self):
        """Retrieve all canister types"""
        from database_model import CanisterType
        return list(CanisterType.select())

    def read_canister_type_by_id(self, type_id):
        """Retrieve a single canister type by ID"""
        from database_model import CanisterType
        return CanisterType.get_or_none(CanisterType.id == type_id)

    def write_canister_type(self, type_data):
        """Create a new canister type (or get existing)"""
        from database_model import CanisterType
        try:
            with self.database.atomic():
                canister_type, created = CanisterType.get_or_create(
                    name=type_data["name"],
                    defaults={
                        "full_weight": type_data["full_weight"],
                        "empty_weight": type_data["empty_weight"]
                    }
                )
                if created:
                    return True, f"Canister type '{type_data['name']}' created"
                else:
                    return True, f"Canister type '{type_data['name']}' already exists"
        except peewee.OperationalError as error:
            return False, f"Failed to create canister type: {str(error)}"

    def delete_canister_type(self, type_id):
        """Delete a canister type (protected types cannot be deleted)"""
        from database_model import CanisterType
        PROTECTED_TYPES = {'Coleman 240g', 'Coleman 450g'}

        try:
            canister_type = CanisterType.get_or_none(CanisterType.id == type_id)
            if not canister_type:
                return False, "Canister type not found"

            if canister_type.name in PROTECTED_TYPES:
                return False, f"Cannot delete protected type '{canister_type.name}'"

            with self.database.atomic():
                canister_type.delete_instance()
            return True, f"Canister type '{canister_type.name}' deleted"
        except peewee.OperationalError as error:
            return False, f"Failed to delete canister type: {str(error)}"

    # ========== Canister Operations ==========

    def read_all_canisters(self):
        """Retrieve all canisters"""
        from database_model import Canister
        return list(Canister.select())

    def read_single_canister(self, canister_id):
        """Retrieve a single canister by ID"""
        from database_model import Canister
        return Canister.get_or_none(Canister.id == canister_id)

    def write_canister(self, canister_data):
        """Create a new canister"""
        from database_model import Canister
        try:
            with self.database.atomic():
                Canister.create(**canister_data)
            return True, "Canister created successfully"
        except peewee.OperationalError as error:
            return False, f"Failed to create canister: {str(error)}"

    def update_canister_label(self, canister_id, new_label):
        """Update a canister's label"""
        from database_model import Canister
        try:
            with self.database.atomic():
                Canister.update(label=new_label.strip()).where(
                    Canister.id == canister_id
                ).execute()
            return True, "Canister label updated"
        except peewee.OperationalError as error:
            return False, f"Failed to update label: {str(error)}"

    def update_canister_status(self, canister_id, new_status):
        """Update a canister's status"""
        from database_model import Canister
        try:
            with self.database.atomic():
                Canister.update(status=new_status).where(
                    Canister.id == canister_id
                ).execute()
            return True, f"Canister status updated to {new_status}"
        except peewee.OperationalError as error:
            return False, f"Failed to update status: {str(error)}"

    def delete_canister(self, canister_id):
        """Delete a canister and all its weighings"""
        from database_model import Canister, Weighing
        try:
            with self.database.atomic():
                # Cascade delete weighings first
                Weighing.delete().where(Weighing.canister_id == canister_id).execute()
                # Then delete canister
                Canister.delete().where(Canister.id == canister_id).execute()
            return True, "Canister deleted successfully"
        except peewee.OperationalError as error:
            return False, f"Failed to delete canister: {str(error)}"

    # ========== Weighing Operations ==========

    def read_weighings_for_canister(self, canister_id):
        """Retrieve all weighings for a specific canister, ordered by date descending"""
        from database_model import Weighing
        return list(
            Weighing.select()
            .where(Weighing.canister_id == canister_id)
            .order_by(Weighing.recorded_at.desc())
        )

    def read_latest_weighing(self, canister_id):
        """Retrieve the latest weighing for a specific canister"""
        from database_model import Weighing
        return (
            Weighing.select()
            .where(Weighing.canister_id == canister_id)
            .order_by(Weighing.recorded_at.desc())
            .first()
        )

    def read_weighing_by_id(self, weighing_id):
        """Retrieve a single weighing by ID"""
        from database_model import Weighing
        return Weighing.get_or_none(Weighing.id == weighing_id)

    def write_weighing(self, weighing_data):
        """Create a new weighing record"""
        from database_model import Weighing
        try:
            with self.database.atomic():
                weighing = Weighing.create(**weighing_data)
            return True, f"Weighing created successfully (ID: {weighing.id})"
        except peewee.OperationalError as error:
            return False, f"Failed to create weighing: {str(error)}"

    def delete_weighing(self, weighing_id):
        """Delete a single weighing record"""
        from database_model import Weighing
        try:
            with self.database.atomic():
                Weighing.delete().where(Weighing.id == weighing_id).execute()
            return True, "Weighing deleted successfully"
        except peewee.OperationalError as error:
            return False, f"Failed to delete weighing: {str(error)}"

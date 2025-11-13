"""
Business logic layer for Gas Gauge application.
Handles calculations, orchestration, and data transformations.
Never touches database directly - only through database_manager.
"""

import logging
from datetime import datetime
from utils import generate_canister_id
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class BusinessLogic:
    def __init__(self):
        self.db_manager = DatabaseManager()

    # ========== Calculations ==========

    def calculate_gas_capacity(self, full_weight, empty_weight):
        """Calculate gas capacity from weights"""
        return full_weight - empty_weight

    def calculate_remaining_gas(self, weight, empty_weight):
        """Calculate remaining gas from current weight"""
        return weight - empty_weight

    def calculate_remaining_percentage(self, weight, empty_weight, gas_capacity):
        """Calculate remaining gas percentage"""
        if gas_capacity <= 0:
            return 0
        remaining_gas = weight - empty_weight
        percentage = (remaining_gas / gas_capacity) * 100
        return max(0, min(percentage, 100))

    def calculate_consumption_percentage(self, remaining_percentage):
        """Calculate consumption percentage"""
        return 100 - remaining_percentage

    def get_status_class(self, percentage):
        """Get CSS class for percentage-based status"""
        if percentage is None:
            return "none"
        if percentage > 50:
            return "high"
        elif percentage > 25:
            return "medium"
        else:
            return "low"

    # ========== Orchestration ==========

    def get_dashboard_data(self):
        """Get all data for dashboard view"""
        canisters = self.db_manager.read_all_canisters()
        canister_types = self.db_manager.read_all_canister_types()

        canister_data = []
        for canister in canisters:
            # Get canister type
            canister_type = self.db_manager.read_canister_type_by_id(canister.canister_type_id)

            # Get latest weighing
            latest_weighing = self.db_manager.read_latest_weighing(canister.id)

            # Calculate percentage if weighing exists
            if latest_weighing and canister_type:
                gas_capacity = self.calculate_gas_capacity(
                    canister_type.full_weight,
                    canister_type.empty_weight
                )
                remaining_percentage = self.calculate_remaining_percentage(
                    latest_weighing.weight,
                    canister_type.empty_weight,
                    gas_capacity
                )
                status_class = self.get_status_class(remaining_percentage)
            else:
                remaining_percentage = None
                status_class = "none"

            canister_data.append({
                "canister": canister,
                "canister_type": canister_type,
                "latest_weighing": latest_weighing,
                "remaining_percentage": remaining_percentage,
                "status_class": status_class,
                "is_depleted": canister.status == "depleted"
            })

        # Sort: active first, then depleted
        canister_data.sort(key=lambda x: (x["is_depleted"], x["canister"].label))

        suggested_label = generate_canister_id()[:7]

        return {
            "canisters": canister_data,
            "canister_types": canister_types,
            "suggested_label": suggested_label
        }

    def get_canister_detail_data(self, canister_id):
        """Get all data for canister detail view"""
        canister = self.db_manager.read_single_canister(canister_id)
        if not canister:
            return None

        canister_type = self.db_manager.read_canister_type_by_id(canister.canister_type_id)
        weighings_raw = self.db_manager.read_weighings_for_canister(canister_id)

        # Enrich weighings with calculations
        weighings = []
        for w in weighings_raw:
            gas_capacity = self.calculate_gas_capacity(
                canister_type.full_weight,
                canister_type.empty_weight
            )
            remaining_gas = self.calculate_remaining_gas(w.weight, canister_type.empty_weight)
            remaining_percentage = self.calculate_remaining_percentage(
                w.weight,
                canister_type.empty_weight,
                gas_capacity
            )
            consumption_percentage = self.calculate_consumption_percentage(remaining_percentage)

            weighings.append({
                "id": w.id,
                "weight": w.weight,
                "comment": w.comment,
                "recorded_at": w.recorded_at,
                "remaining_gas": remaining_gas,
                "remaining_percentage": remaining_percentage,
                "consumption_percentage": consumption_percentage
            })

        latest_weighing = weighings[0] if weighings else None
        status_class = self.get_status_class(
            latest_weighing["remaining_percentage"] if latest_weighing else None
        )

        return {
            "canister": canister,
            "canister_type": canister_type,
            "weighings": weighings,
            "latest_weighing": latest_weighing,
            "status_class": status_class
        }

    # ========== Create Operations ==========

    def create_canister(self, label, canister_type_id):
        """Create a new canister"""
        canister_id = generate_canister_id()
        canister_data = {
            "id": canister_id,
            "label": label.strip(),
            "canister_type_id": canister_type_id,
            "status": "active",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        success, message = self.db_manager.write_canister(canister_data)
        if success:
            logger.info(f"Created canister '{label}' with ID {canister_id}")
        return success, message

    def create_weighing(self, canister_id, weight, recorded_at_str, comment):
        """Create a new weighing record"""
        weighing_data = {
            "canister_id": canister_id,
            "weight": weight,
            "recorded_at": recorded_at_str,
            "comment": comment
        }
        success, message = self.db_manager.write_weighing(weighing_data)
        if success:
            logger.info(f"Created weighing for canister {canister_id}: {weight}g")
        return success, message

    def create_canister_type(self, name, full_weight, empty_weight):
        """Create a new canister type"""
        type_data = {
            "name": name,
            "full_weight": full_weight,
            "empty_weight": empty_weight
        }
        success, message = self.db_manager.write_canister_type(type_data)
        if success:
            logger.info(f"Created canister type '{name}'")
        return success, message

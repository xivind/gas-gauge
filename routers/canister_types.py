from fastapi import APIRouter, HTTPException
from schemas import CanisterTypeCreate, CanisterTypeResponse
import logging
import database_manager as db_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/canister-types", tags=["canister-types"])

@router.post("", response_model=CanisterTypeResponse)
def create_canister_type_api(canister_type: CanisterTypeCreate):
    """Create a new canister type via API"""
    try:
        ct = db_manager.create_canister_type(
            name=canister_type.name,
            full_weight=canister_type.full_weight,
            empty_weight=canister_type.empty_weight
        )
        return {
            "id": ct.id,
            "name": ct.name,
            "full_weight": ct.full_weight,
            "empty_weight": ct.empty_weight,
            "gas_capacity": ct.gas_capacity
        }
    except Exception as e:
        logger.error(f"API Error creating canister type: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[CanisterTypeResponse])
def list_canister_types_api():
    """List all canister types via API"""
    types = db_manager.get_all_canister_types()
    return [{
        "id": ct.id,
        "name": ct.name,
        "full_weight": ct.full_weight,
        "empty_weight": ct.empty_weight,
        "gas_capacity": ct.gas_capacity
    } for ct in types]

@router.delete("/{type_id}")
def delete_canister_type_api(type_id: int):
    """Delete a canister type via API"""
    try:
        # The manager handles the logic of checking for existence and if it's a protected type
        db_manager.delete_canister_type(type_id)
        return {"success": True}
    except Exception as e:
        # Catch potential errors from the manager, e.g., if the type is protected
        logger.error(f"API Error deleting canister type {type_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

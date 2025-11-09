from fastapi import APIRouter, HTTPException
from models import CanisterType
from schemas import CanisterTypeCreate, CanisterTypeResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/canister-types", tags=["canister-types"])

@router.post("", response_model=CanisterTypeResponse)
def create_canister_type(canister_type: CanisterTypeCreate):
    """Create a new canister type"""
    try:
        ct = CanisterType.create(**canister_type.model_dump())
        logger.info(f"Created canister type: {ct.name}")
        return {
            "id": ct.id,
            "name": ct.name,
            "full_weight": ct.full_weight,
            "empty_weight": ct.empty_weight,
            "gas_capacity": ct.gas_capacity
        }
    except Exception as e:
        logger.error(f"Error creating canister type: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[CanisterTypeResponse])
def list_canister_types():
    """List all canister types"""
    types = CanisterType.select()
    return [{
        "id": ct.id,
        "name": ct.name,
        "full_weight": ct.full_weight,
        "empty_weight": ct.empty_weight,
        "gas_capacity": ct.gas_capacity
    } for ct in types]

@router.delete("/{type_id}")
def delete_canister_type(type_id: int):
    """Delete a canister type"""
    try:
        ct = CanisterType.get_by_id(type_id)
        ct.delete_instance()
        logger.info(f"Deleted canister type: {ct.name}")
        return {"success": True}
    except CanisterType.DoesNotExist:
        raise HTTPException(status_code=404, detail="Canister type not found")

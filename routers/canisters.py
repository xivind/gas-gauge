from fastapi import APIRouter, HTTPException, Query
from models import Canister, CanisterType
from schemas import CanisterCreate, CanisterResponse
from typing import Optional
from utils import generate_canister_id
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/canisters", tags=["canisters"])

@router.post("", response_model=CanisterResponse)
def create_canister(canister: CanisterCreate):
    """Create a new canister"""
    try:
        # Validate label
        if not canister.label or canister.label.strip() == "":
            raise HTTPException(status_code=400, detail="Label cannot be empty")

        if len(canister.label) > 64:
            raise HTTPException(status_code=400, detail="Label cannot exceed 64 characters")

        # Verify canister type exists
        CanisterType.get_by_id(canister.canister_type_id)

        # Generate UUID-based ID
        canister_id = generate_canister_id()

        # Create canister with generated ID
        c = Canister.create(
            id=canister_id,
            label=canister.label,
            canister_type_id=canister.canister_type_id
        )
        logger.info(f"Created canister: {c.id} ({c.label})")
        return {
            "id": c.id,
            "label": c.label,
            "canister_type_id": c.canister_type_id,
            "status": c.status,
            "created_at": c.created_at
        }
    except CanisterType.DoesNotExist:
        raise HTTPException(status_code=404, detail="Canister type not found")
    except Exception as e:
        logger.error(f"Error creating canister: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[CanisterResponse])
def list_canisters(status: Optional[str] = Query(None)):
    """List canisters, optionally filtered by status"""
    query = Canister.select()
    if status:
        query = query.where(Canister.status == status)

    return [{
        "id": c.id,
        "label": c.label,
        "canister_type_id": c.canister_type_id,
        "status": c.status,
        "created_at": c.created_at
    } for c in query]

@router.get("/{canister_id}", response_model=CanisterResponse)
def get_canister(canister_id: str):  # Changed from int to str
    """Get a single canister by ID"""
    try:
        c = Canister.get_by_id(canister_id)
        return {
            "id": c.id,
            "label": c.label,
            "canister_type_id": c.canister_type_id,
            "status": c.status,
            "created_at": c.created_at
        }
    except Canister.DoesNotExist:
        raise HTTPException(status_code=404, detail="Canister not found")

@router.patch("/{canister_id}/status")
def update_canister_status(canister_id: str, status_update: dict):  # Changed from int to str
    """Update canister status (active/depleted)"""
    try:
        c = Canister.get_by_id(canister_id)
        new_status = status_update.get("status")

        if new_status not in ["active", "depleted"]:
            raise HTTPException(status_code=400, detail="Invalid status")

        c.status = new_status
        c.save()
        logger.info(f"Updated canister {c.id} ({c.label}) status to {new_status}")

        return {"success": True}
    except Canister.DoesNotExist:
        raise HTTPException(status_code=404, detail="Canister not found")

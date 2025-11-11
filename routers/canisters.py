from fastapi import APIRouter, HTTPException, Query
from schemas import CanisterCreate, CanisterResponse
from typing import Optional
import logging
import database_manager as db_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/canisters", tags=["canisters"])

@router.post("", response_model=CanisterResponse)
def create_canister_api(canister: CanisterCreate):
    """Create a new canister via API"""
    if not canister.label or not canister.label.strip() or len(canister.label) > 64:
        raise HTTPException(status_code=400, detail="Invalid label")
    
    try:
        # Verify canister type exists by trying to fetch it
        if not db_manager.get_canister_type_by_id(canister.canister_type_id):
             raise HTTPException(status_code=404, detail="Canister type not found")

        c = db_manager.create_canister(canister.label, canister.canister_type_id)
        return {
            "id": c.id,
            "label": c.label,
            "canister_type_id": c.canister_type_id,
            "status": c.status,
            "created_at": c.created_at
        }
    except Exception as e:
        logger.error(f"API Error creating canister: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("", response_model=list[CanisterResponse])
def list_canisters_api(status: Optional[str] = Query(None)):
    """List canisters via API, optionally filtered by status"""
    canisters = db_manager.get_all_canisters()
    if status:
        canisters = [c for c in canisters if c.status == status]

    return [{
        "id": c.id,
        "label": c.label,
        "canister_type_id": c.canister_type_id,
        "status": c.status,
        "created_at": c.created_at
    } for c in canisters]

@router.get("/{canister_id}", response_model=CanisterResponse)
def get_canister_api(canister_id: str):
    """Get a single canister by ID via API"""
    canister = db_manager.get_canister_by_id(canister_id)
    if not canister:
        raise HTTPException(status_code=404, detail="Canister not found")
    
    return {
        "id": canister.id,
        "label": canister.label,
        "canister_type_id": canister.canister_type_id,
        "status": canister.status,
        "created_at": canister.created_at
    }

@router.patch("/{canister_id}/status")
def update_canister_status_api(canister_id: str, status_update: dict):
    """Update canister status via API"""
    new_status = status_update.get("status")
    if new_status not in ["active", "depleted"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    canister = db_manager.get_canister_by_id(canister_id)
    if not canister:
        raise HTTPException(status_code=404, detail="Canister not found")

    db_manager.update_canister_status(canister_id, new_status)
    return {"success": True}

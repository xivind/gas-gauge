from fastapi import APIRouter, HTTPException, Query
from schemas import WeighingCreate, WeighingResponse
from typing import Optional
import logging
import database_manager as db_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/weighings", tags=["weighings"])

@router.post("", response_model=WeighingResponse)
def create_weighing_api(weighing: WeighingCreate):
    """Create a new weighing record via API"""
    try:
        w = db_manager.create_weighing(
            canister_id=weighing.canister_id,
            weight=weighing.weight,
            recorded_at=weighing.recorded_at,
            comment=weighing.comment
        )
        return {
            "id": w.id,
            "canister_id": w.canister.id,
            "weight": w.weight,
            "comment": w.comment,
            "recorded_at": w.recorded_at,
            "remaining_gas": w.remaining_gas,
            "remaining_percentage": w.remaining_percentage,
            "consumption_percentage": w.consumption_percentage
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"API Error creating weighing: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[WeighingResponse])
def list_weighings_api(canister_id: Optional[str] = Query(None)):
    """List weighings via API, optionally filtered by canister"""
    if canister_id:
        canister = db_manager.get_canister_by_id(canister_id)
        if not canister:
            return [] # Or raise HTTPException(status_code=404, detail="Canister not found")
        weighings = db_manager.get_weighings_by_canister(canister)
    else:
        # This could be inefficient, but we'll allow it.
        # A better approach for a large dataset would be to get all canisters
        # and then get weighings for each.
        all_canisters = db_manager.get_all_canisters()
        weighings = []
        for c in all_canisters:
            weighings.extend(db_manager.get_weighings_by_canister(c))
        # Sort by date as the manager only sorts within a canister's weighings
        weighings.sort(key=lambda w: w.recorded_at, reverse=True)

    return [{
        "id": w.id,
        "canister_id": w.canister.id,
        "weight": w.weight,
        "comment": w.comment,
        "recorded_at": w.recorded_at,
        "remaining_gas": w.remaining_gas,
        "remaining_percentage": w.remaining_percentage,
        "consumption_percentage": w.consumption_percentage
    } for w in weighings]

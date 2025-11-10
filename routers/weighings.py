from fastapi import APIRouter, HTTPException, Query
from models import Weighing, Canister
from schemas import WeighingCreate, WeighingResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/weighings", tags=["weighings"])

@router.post("", response_model=WeighingResponse)
def create_weighing(weighing: WeighingCreate):
    """Create a new weighing record"""
    try:
        # Verify canister exists
        canister = Canister.get_by_id(weighing.canister_id)

        w = Weighing.create(**weighing.model_dump())
        logger.info(f"Created weighing for canister {canister.id} ({canister.label}): {w.weight}g")

        return {
            "id": w.id,
            "canister_id": w.canister_id,
            "weight": w.weight,
            "comment": w.comment,
            "recorded_at": w.recorded_at,
            "remaining_gas": w.remaining_gas,
            "remaining_percentage": w.remaining_percentage,
            "consumption_percentage": w.consumption_percentage
        }
    except Canister.DoesNotExist:
        raise HTTPException(status_code=404, detail="Canister not found")
    except Exception as e:
        logger.error(f"Error creating weighing: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[WeighingResponse])
def list_weighings(canister_id: Optional[str] = Query(None)):
    """List weighings, optionally filtered by canister"""
    query = Weighing.select()
    if canister_id:
        query = query.where(Weighing.canister_id == canister_id)

    query = query.order_by(Weighing.recorded_at.desc())

    return [{
        "id": w.id,
        "canister_id": w.canister_id,
        "weight": w.weight,
        "comment": w.comment,
        "recorded_at": w.recorded_at,
        "remaining_gas": w.remaining_gas,
        "remaining_percentage": w.remaining_percentage,
        "consumption_percentage": w.consumption_percentage
    } for w in query]

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CanisterTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    full_weight: int = Field(..., gt=0)
    empty_weight: int = Field(..., gt=0)

class CanisterTypeResponse(BaseModel):
    id: int
    name: str
    full_weight: int
    empty_weight: int
    gas_capacity: int

class CanisterCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    canister_type_id: int

class CanisterResponse(BaseModel):
    id: int
    label: str
    canister_type_id: int
    status: str
    created_at: datetime

class WeighingCreate(BaseModel):
    canister_id: int
    weight: int = Field(..., gt=0)
    comment: Optional[str] = None

class WeighingResponse(BaseModel):
    id: int
    canister_id: int
    weight: int
    comment: Optional[str]
    recorded_at: datetime
    remaining_gas: int
    remaining_percentage: float
    consumption_percentage: float

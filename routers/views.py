from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models import Canister, CanisterType, Weighing
from utils import generate_canister_id
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")
router = APIRouter()

def get_status_class(percentage):
    """Get CSS class for percentage"""
    if percentage > 50:
        return "high"
    elif percentage > 25:
        return "medium"
    else:
        return "low"

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """Dashboard showing all canisters with toggle for depleted"""
    # Get all canisters (both active and depleted)
    canisters = Canister.select()
    canister_types = CanisterType.select()

    canister_data = []
    for canister in canisters:
        latest_weighing = (Weighing
                          .select()
                          .where(Weighing.canister == canister)
                          .order_by(Weighing.recorded_at.desc())
                          .first())

        if not latest_weighing:
            status_class = "none"  # No measurements yet - gray
        else:
            status_class = get_status_class(latest_weighing.remaining_percentage)

        canister_data.append({
            "canister": canister,
            "latest_weighing": latest_weighing,
            "status_class": status_class,
            "is_depleted": canister.status == "depleted"
        })

    # Sort canisters: active first, then depleted
    canister_data.sort(key=lambda x: (x["is_depleted"], x["canister"].label))

    # Generate suggested label for new canister (trimmed for user display)
    suggested_label = generate_canister_id()[:7]  # GC- + first 4 chars only

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "canisters": canister_data,
        "canister_types": canister_types,
        "suggested_label": suggested_label
    })

@router.post("/canister/create")
def create_canister_form(label: str = Form(...), canister_type_id: int = Form(...)):
    """Create canister from form submission"""
    Canister.create(label=label, canister_type_id=canister_type_id)
    return RedirectResponse(url="/", status_code=303)

@router.get("/canister/{canister_id}", response_class=HTMLResponse)
def canister_detail(request: Request, canister_id: str):
    """Canister detail page with weighing history"""
    try:
        canister = Canister.get_by_id(canister_id)
    except Canister.DoesNotExist:
        return RedirectResponse(url="/", status_code=303)

    weighings = (Weighing
                .select()
                .where(Weighing.canister == canister)
                .order_by(Weighing.recorded_at.desc()))

    latest_weighing = weighings.first() if weighings else None
    if not latest_weighing:
        status_class = "none"  # No measurements yet - gray
    else:
        status_class = get_status_class(latest_weighing.remaining_percentage)

    return templates.TemplateResponse("canister_detail.html", {
        "request": request,
        "canister": canister,
        "weighings": weighings,
        "latest_weighing": latest_weighing,
        "status_class": status_class
    })

@router.post("/canister/{canister_id}/add-weighing")
def add_weighing_form(
    canister_id: str,
    weight: int = Form(...),
    recorded_at: str = Form(...),
    comment: str = Form(None)
):
    """Add weighing from form submission"""
    # Parse date string (format: YYYY-MM-DD)
    recorded_datetime = datetime.strptime(recorded_at, "%Y-%m-%d")

    # Get the canister object
    canister = Canister.get_by_id(canister_id)

    # Create weighing with canister object (not canister_id)
    weighing = Weighing.create(
        canister=canister,
        weight=weight,
        recorded_at=recorded_datetime,
        comment=comment
    )
    logger.info(f"Created weighing {weighing.id} for canister {canister.id} ({canister.label}): {weight}g")
    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@router.post("/canister/{canister_id}/mark-depleted")
def mark_canister_depleted(canister_id: str):
    """Mark canister as depleted"""
    canister = Canister.get_by_id(canister_id)
    canister.status = "depleted"
    canister.save()
    return RedirectResponse(url="/", status_code=303)

@router.post("/canister/{canister_id}/reactivate")
def reactivate_canister(canister_id: str):
    """Reactivate a depleted canister"""
    canister = Canister.get_by_id(canister_id)
    canister.status = "active"
    canister.save()
    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@router.post("/canister/{canister_id}/delete")
def delete_canister(canister_id: str):
    """Delete canister and all its weighings"""
    try:
        canister = Canister.get_by_id(canister_id)
        label = canister.label
        canister_id_str = canister.id

        # Delete all weighings first (cascade)
        Weighing.delete().where(Weighing.canister == canister).execute()

        # Delete the canister
        canister.delete_instance()

        logger.info(f"Deleted canister {canister_id_str} ({label}) and all weighings")
        return RedirectResponse(url="/", status_code=303)
    except Canister.DoesNotExist:
        raise HTTPException(status_code=404, detail="Canister not found")

@router.post("/canister/{canister_id}/update-label", response_class=RedirectResponse)
def update_canister_label(canister_id: str, label: str = Form(...)):
    """Update canister label"""
    try:
        # Validate label
        if not label or label.strip() == "":
            raise HTTPException(status_code=400, detail="Label cannot be empty")

        if len(label) > 64:
            raise HTTPException(status_code=400, detail="Label cannot exceed 64 characters")

        canister = Canister.get_by_id(canister_id)
        old_label = canister.label
        canister.label = label.strip()
        canister.save()

        logger.info(f"Updated canister {canister_id} label from '{old_label}' to '{label}'")
        return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)
    except Canister.DoesNotExist:
        raise HTTPException(status_code=404, detail="Canister not found")

@router.post("/weighing/{weighing_id}/delete")
def delete_weighing(weighing_id: int):
    """Delete a weighing record"""
    try:
        weighing = Weighing.get_by_id(weighing_id)
        canister_id = weighing.canister.id
        weighing.delete_instance()
        return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)
    except Weighing.DoesNotExist:
        return RedirectResponse(url="/", status_code=303)

@router.get("/admin/types", response_class=HTMLResponse)
def admin_types(request: Request):
    """Admin page for managing canister types"""
    canister_types = CanisterType.select()

    return templates.TemplateResponse("admin/types.html", {
        "request": request,
        "canister_types": canister_types
    })

@router.post("/admin/types/create")
def create_type_form(
    name: str = Form(...),
    full_weight: int = Form(...),
    empty_weight: int = Form(...)
):
    """Create canister type from form submission"""
    CanisterType.create(name=name, full_weight=full_weight, empty_weight=empty_weight)
    return RedirectResponse(url="/admin/types", status_code=303)

@router.post("/admin/types/{type_id}/delete")
def delete_type_form(type_id: int):
    """Delete canister type"""
    ct = CanisterType.get_by_id(type_id)
    # Prevent deletion of built-in types
    if ct.name not in ['Coleman 240g', 'Coleman 450g']:
        ct.delete_instance()
    return RedirectResponse(url="/admin/types", status_code=303)

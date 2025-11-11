from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import logging
import database_manager as db_manager
from utils import generate_canister_id

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")
router = APIRouter()

def get_status_class(percentage):
    """Get CSS class for percentage"""
    if percentage is None:
        return "none"
    if percentage > 50:
        return "high"
    elif percentage > 25:
        return "medium"
    else:
        return "low"

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """Dashboard showing all canisters with toggle for depleted"""
    canisters = db_manager.get_all_canisters()
    canister_types = db_manager.get_all_canister_types()

    canister_data = []
    for canister in canisters:
        latest_weighing = db_manager.get_latest_weighing(canister)
        status_class = get_status_class(latest_weighing.remaining_percentage if latest_weighing else None)

        canister_data.append({
            "canister": canister,
            "latest_weighing": latest_weighing,
            "status_class": status_class,
            "is_depleted": canister.status == "depleted"
        })

    # Sort canisters: active first, then depleted
    canister_data.sort(key=lambda x: (x["is_depleted"], x["canister"].label))
    suggested_label = generate_canister_id()[:7]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "canisters": canister_data,
        "canister_types": canister_types,
        "suggested_label": suggested_label
    })

@router.post("/canister/create")
def create_canister_form(label: str = Form(...), canister_type_id: int = Form(...)):
    """Create canister from form submission"""
    db_manager.create_canister(label, canister_type_id)
    return RedirectResponse(url="/", status_code=303)

@router.get("/canister/{canister_id}", response_class=HTMLResponse)
def canister_detail(request: Request, canister_id: str):
    """Canister detail page with weighing history"""
    canister = db_manager.get_canister_by_id(canister_id)
    if not canister:
        return RedirectResponse(url="/", status_code=303)

    weighings = db_manager.get_weighings_by_canister(canister)
    latest_weighing = weighings[0] if weighings else None
    status_class = get_status_class(latest_weighing.remaining_percentage if latest_weighing else None)

    return templates.TemplateResponse("canister_detail.html", {
        "request": request,
        "canister": canister,
        "weighings": weighings,
        "latest_weighing": latest_weighing,
        "status_class": status_class
    })

@router.post("/canister/{canister_id}/add-weighing")
def add_weighing_form(canister_id: str, weight: int = Form(...), recorded_at: str = Form(...), comment: str = Form(None)):
    """Add weighing from form submission"""
    recorded_datetime = datetime.strptime(recorded_at, "%Y-%m-%d")
    db_manager.create_weighing(canister_id, weight, recorded_datetime, comment)
    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@router.post("/canister/{canister_id}/mark-depleted")
def mark_canister_depleted(canister_id: str):
    """Mark canister as depleted"""
    db_manager.update_canister_status(canister_id, "depleted")
    return RedirectResponse(url="/", status_code=303)

@router.post("/canister/{canister_id}/reactivate")
def reactivate_canister(canister_id: str):
    """Reactivate a depleted canister"""
    db_manager.update_canister_status(canister_id, "active")
    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@router.post("/canister/{canister_id}/delete")
def delete_canister_route(canister_id: str):
    """Delete canister and all its weighings"""
    db_manager.delete_canister(canister_id)
    return RedirectResponse(url="/", status_code=303)

@router.post("/canister/{canister_id}/update-label", response_class=RedirectResponse)
def update_canister_label_route(canister_id: str, label: str = Form(...)):
    """Update canister label"""
    if not label or not label.strip() or len(label) > 64:
        raise HTTPException(status_code=400, detail="Invalid label")
    db_manager.update_canister_label(canister_id, label)
    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@router.post("/weighing/{weighing_id}/delete")
def delete_weighing_route(weighing_id: str):
    """Delete a weighing record"""
    weighing = db_manager.get_weighing_by_id(weighing_id)
    if weighing:
        canister_id = weighing.canister.id
        db_manager.delete_weighing(weighing_id)
        return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)
    return RedirectResponse(url="/", status_code=303)

@router.get("/admin/types", response_class=HTMLResponse)
def admin_types(request: Request):
    """Admin page for managing canister types"""
    canister_types = db_manager.get_all_canister_types()
    return templates.TemplateResponse("admin/types.html", {
        "request": request,
        "canister_types": canister_types
    })

@router.post("/admin/types/create")
def create_type_form(name: str = Form(...), full_weight: int = Form(...), empty_weight: int = Form(...)):
    """Create canister type from form submission"""
    db_manager.create_canister_type(name, full_weight, empty_weight)
    return RedirectResponse(url="/admin/types", status_code=303)

@router.post("/admin/types/{type_id}/delete")
def delete_type_form(type_id: int):
    """Delete canister type"""
    db_manager.delete_canister_type(type_id)
    return RedirectResponse(url="/admin/types", status_code=303)

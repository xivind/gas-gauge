from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models import Canister, CanisterType, Weighing

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
    """Dashboard showing active canisters"""
    canisters = Canister.select().where(Canister.status == "active")
    canister_types = CanisterType.select()

    canister_data = []
    for canister in canisters:
        latest_weighing = (Weighing
                          .select()
                          .where(Weighing.canister == canister)
                          .order_by(Weighing.recorded_at.desc())
                          .first())

        status_class = "low"
        if latest_weighing:
            status_class = get_status_class(latest_weighing.remaining_percentage)

        canister_data.append({
            "canister": canister,
            "latest_weighing": latest_weighing,
            "status_class": status_class
        })

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "canisters": canister_data,
        "canister_types": canister_types
    })

@router.post("/canister/create")
def create_canister_form(label: str = Form(...), canister_type_id: int = Form(...)):
    """Create canister from form submission"""
    Canister.create(label=label, canister_type_id=canister_type_id)
    return RedirectResponse(url="/", status_code=303)

@router.get("/canister/{canister_id}", response_class=HTMLResponse)
def canister_detail(request: Request, canister_id: int):
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
    status_class = "low"
    if latest_weighing:
        status_class = get_status_class(latest_weighing.remaining_percentage)

    return templates.TemplateResponse("canister_detail.html", {
        "request": request,
        "canister": canister,
        "weighings": weighings,
        "latest_weighing": latest_weighing,
        "status_class": status_class
    })

@router.post("/canister/{canister_id}/add-weighing")
def add_weighing_form(canister_id: int, weight: int = Form(...), comment: str = Form(None)):
    """Add weighing from form submission"""
    Weighing.create(canister_id=canister_id, weight=weight, comment=comment)
    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@router.post("/canister/{canister_id}/mark-depleted")
def mark_canister_depleted(canister_id: int):
    """Mark canister as depleted"""
    canister = Canister.get_by_id(canister_id)
    canister.status = "depleted"
    canister.save()
    return RedirectResponse(url="/", status_code=303)

@router.post("/canister/{canister_id}/reactivate")
def reactivate_canister(canister_id: int):
    """Reactivate a depleted canister"""
    canister = Canister.get_by_id(canister_id)
    canister.status = "active"
    canister.save()
    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@router.get("/archive", response_class=HTMLResponse)
def archive(request: Request):
    """Archive page showing depleted canisters"""
    canisters = Canister.select().where(Canister.status == "depleted")

    canister_data = []
    for canister in canisters:
        latest_weighing = (Weighing
                          .select()
                          .where(Weighing.canister == canister)
                          .order_by(Weighing.recorded_at.desc())
                          .first())

        weighing_count = Weighing.select().where(Weighing.canister == canister).count()

        canister_data.append({
            "canister": canister,
            "latest_weighing": latest_weighing,
            "weighing_count": weighing_count
        })

    return templates.TemplateResponse("archive.html", {
        "request": request,
        "canisters": canister_data
    })

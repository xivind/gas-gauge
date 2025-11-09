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

"""
Main application file for Gas Gauge.
All routes consolidated here - no separate router files.
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from logger import setup_logging
from business_logic import BusinessLogic
from seed_data import seed_canister_types
import logging

# Setup logging
logger = setup_logging()

# Initialize app
app = FastAPI(title="Gas Gauge")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database and seed data
logger.info("Initializing database...")
business_logic = BusinessLogic()
business_logic.db_manager.init_db()
seed_canister_types()
logger.info("Database initialized")

def health_check():
    """Test database connectivity and write healthcheck status"""
    try:
        # Test database connectivity with a simple query
        from database_model import CanisterType
        CanisterType.select().limit(1).execute()
        with open("status.txt", "w", encoding='utf-8') as file:
            file.write("ok")
        logger.info("Health check passed")
        return True
    except Exception as error:
        logger.error(f"Health check failed: {error}")
        with open("status.txt", "w", encoding='utf-8') as file:
            file.write("error")
        return False

# Perform startup health check
logger.info("Performing startup health check...")
health_check()

# ==================== HTML VIEWS ====================

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """Dashboard showing all canisters with toggle for depleted"""
    payload = business_logic.get_dashboard_data()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "canisters": payload["canisters"],
        "canister_types": payload["canister_types"],
        "suggested_label": payload["suggested_label"]
    })

@app.get("/canister/{canister_id}", response_class=HTMLResponse)
def canister_detail(request: Request, canister_id: str):
    """Canister detail page with weighing history"""
    payload = business_logic.get_canister_detail_data(canister_id)
    if not payload:
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse("canister_detail.html", {
        "request": request,
        **payload
    })

@app.get("/admin/types", response_class=HTMLResponse)
def admin_types(request: Request):
    """Admin page for managing canister types"""
    canister_types = business_logic.db_manager.read_all_canister_types()
    return templates.TemplateResponse("admin/types.html", {
        "request": request,
        "canister_types": canister_types
    })

# ==================== FORM SUBMISSIONS ====================

@app.post("/canister/create")
def create_canister_form(
    label: str = Form(...),
    canister_type_id: int = Form(...)
):
    """Create canister from form"""
    if not label or len(label.strip()) == 0 or len(label) > 64:
        raise HTTPException(status_code=400, detail="Invalid label: must be 1-64 characters")

    success, message = business_logic.create_canister(label, canister_type_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return RedirectResponse(url="/", status_code=303)

@app.post("/canister/{canister_id}/add-weighing")
def add_weighing_form(
    canister_id: str,
    weight: int = Form(...),
    recorded_at: str = Form(...),
    comment: str = Form(None)
):
    """Add weighing from form"""
    success, message = business_logic.create_weighing(
        canister_id, weight, recorded_at, comment
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@app.post("/canister/{canister_id}/mark-depleted")
def mark_canister_depleted(canister_id: str):
    """Mark canister as depleted"""
    success, message = business_logic.db_manager.update_canister_status(
        canister_id, "depleted"
    )
    if not success:
        logger.warning(f"Failed to mark canister as depleted: {message}")
    return RedirectResponse(url="/", status_code=303)

@app.post("/canister/{canister_id}/reactivate")
def reactivate_canister(canister_id: str):
    """Reactivate depleted canister"""
    success, message = business_logic.db_manager.update_canister_status(
        canister_id, "active"
    )
    if not success:
        logger.warning(f"Failed to reactivate canister: {message}")
    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@app.post("/canister/{canister_id}/delete")
def delete_canister_route(canister_id: str):
    """Delete canister and all its weighings"""
    success, message = business_logic.db_manager.delete_canister(canister_id)
    if not success:
        logger.error(f"Failed to delete canister: {message}")
        raise HTTPException(status_code=400, detail=message)
    return RedirectResponse(url="/", status_code=303)

@app.post("/canister/{canister_id}/update-label")
def update_canister_label_route(
    canister_id: str,
    label: str = Form(...)
):
    """Update canister label"""
    if not label or len(label.strip()) == 0 or len(label) > 64:
        raise HTTPException(status_code=400, detail="Invalid label: must be 1-64 characters")

    success, message = business_logic.db_manager.update_canister_label(
        canister_id, label
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@app.post("/weighing/{weighing_id}/delete")
def delete_weighing_route(weighing_id: int):
    """Delete weighing record"""
    weighing = business_logic.db_manager.read_weighing_by_id(weighing_id)
    if weighing:
        canister_id = weighing.canister_id
        success, message = business_logic.db_manager.delete_weighing(weighing_id)
        if not success:
            logger.error(f"Failed to delete weighing: {message}")
        return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)
    return RedirectResponse(url="/", status_code=303)

@app.post("/admin/types/create")
def create_type_form(
    name: str = Form(...),
    full_weight: int = Form(...),
    empty_weight: int = Form(...)
):
    """Create canister type"""
    if empty_weight >= full_weight:
        raise HTTPException(status_code=400, detail="Empty weight must be less than full weight")

    success, message = business_logic.create_canister_type(
        name, full_weight, empty_weight
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return RedirectResponse(url="/admin/types", status_code=303)

@app.post("/admin/types/{type_id}/delete")
def delete_type_form(type_id: int):
    """Delete canister type"""
    success, message = business_logic.db_manager.delete_canister_type(type_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return RedirectResponse(url="/admin/types", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config="uvicorn_log_config.ini"
    )

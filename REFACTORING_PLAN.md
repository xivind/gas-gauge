# Gas Gauge Refactoring Plan

**Date:** 2025-11-11
**Goal:** Simplify codebase following velo-supervisor-2000 patterns
**Approach:** Remove magic, consolidate files, improve clarity

---

## 📊 Current State

### File Structure (22 Python files)
```
gas-gauge/
├── models.py                    # Peewee models with ForeignKeyField, computed properties
├── schemas.py                   # Pydantic schemas for validation
├── database.py                  # Database initialization
├── database_manager.py          # Database operations (functions)
├── main.py                      # App setup only
├── utils.py                     # Helper functions
├── logger.py                    # Logging setup
├── seed_data.py                 # Seed predefined types
├── recreate_db.py              # Database recreation script
├── routers/
│   ├── __init__.py
│   ├── canister_types.py       # 52 lines - canister type routes
│   ├── canisters.py            # 76 lines - canister routes
│   ├── weighings.py            # 65 lines - weighing routes
│   └── views.py                # 141 lines - HTML views
└── tests/                       # 8 test files (~400 lines)
    ├── conftest.py
    ├── test_models.py
    ├── test_canisters_router.py
    ├── test_canister_types_router.py
    ├── test_weighings_router.py
    ├── test_weighings.py
    ├── test_seed_data.py
    └── test_utils.py
```

### Current Patterns
- **Models:** Use ForeignKeyField with backrefs, computed @property decorators
- **Validation:** Pydantic schemas for API endpoints
- **Routes:** Split across 4 router files
- **Database:** Function-based database_manager
- **Business Logic:** Mixed between models (@property) and database_manager

---

## 🎯 Target State

### File Structure (7 Python files)
```
gas-gauge/
├── database_model.py            # NEW NAME - Simple Peewee models, NO magic
├── database_manager.py          # REFACTORED - Class-based with transactions
├── business_logic.py            # NEW FILE - Calculations and orchestration
├── main.py                      # REFACTORED - All routes consolidated here
├── database.py                  # KEEP - Minor updates
├── utils.py                     # KEEP - As-is
├── logger.py                    # KEEP - As-is
└── seed_data.py                 # UPDATE - Use new patterns
```

### Target Patterns (velo-supervisor-2000 style)
- **Models:** Simple fields only, no ForeignKeyField, no computed properties
- **Validation:** FastAPI Form(...) directly, NO Pydantic schemas
- **Routes:** All in main.py (~400 lines)
- **Database:** Class-based DatabaseManager with atomic transactions
- **Business Logic:** Separate BusinessLogic class for calculations

---

## 📋 Detailed Changes by File

### 1. ❌ DELETE (9 files)

**Remove completely:**
```
schemas.py                       # Pydantic validation removed
recreate_db.py                   # Utility script, not needed
routers/__init__.py              # No routers folder
routers/canister_types.py        # Merged into main.py
routers/canisters.py             # Merged into main.py
routers/weighings.py             # Merged into main.py
routers/views.py                 # Merged into main.py
tests/                           # All 8 test files deleted
```

---

### 2. ✏️ RENAME (1 file)

**models.py → database_model.py**

**Changes to content:**
```python
# BEFORE (models.py):
from peewee import Model, CharField, IntegerField, ForeignKeyField, TextField, DateTimeField, AutoField

class Canister(BaseModel):
    id = CharField(primary_key=True)
    label = CharField(max_length=64)
    canister_type = ForeignKeyField(CanisterType, backref='canisters')  # ← Remove magic
    status = CharField(default='active')
    created_at = DateTimeField(default=datetime.now)

class Weighing(BaseModel):
    id = AutoField()
    canister = ForeignKeyField(Canister, backref='weighings')  # ← Remove magic
    weight = IntegerField()
    comment = TextField(null=True)
    recorded_at = DateTimeField(default=datetime.now)

    @property  # ← Remove computed properties
    def remaining_gas(self):
        return self.weight - self.canister.canister_type.empty_weight
```

```python
# AFTER (database_model.py):
from peewee import Model, CharField, IntegerField, TextField, DateTimeField, AutoField

class CanisterType(BaseModel):
    id = AutoField()
    name = CharField(unique=True)
    full_weight = IntegerField()
    empty_weight = IntegerField()

    class Meta:
        table_name = "canistertype"

class Canister(BaseModel):
    id = CharField(primary_key=True, unique=True)
    label = CharField()
    canister_type_id = IntegerField()  # ← Plain integer
    status = CharField()
    created_at = CharField()  # ← ISO string format

    class Meta:
        table_name = "canister"

class Weighing(BaseModel):
    id = AutoField()
    canister_id = CharField()  # ← Plain string
    weight = IntegerField()
    comment = TextField(null=True)
    recorded_at = CharField()  # ← ISO string format

    class Meta:
        table_name = "weighing"
```

**Key changes:**
- ✅ Remove ForeignKeyField → use IntegerField/CharField for IDs
- ✅ Remove all @property decorators
- ✅ Add explicit table_name in Meta
- ✅ Use CharField for dates (ISO format strings)
- ✅ No default=datetime.now (handle in business logic)

---

### 3. 🔨 REFACTOR database_manager.py

**Convert from functions to class:**

```python
# BEFORE (function-based):
def create_canister(label: str, canister_type_id: int) -> Canister:
    try:
        canister_id = generate_canister_id()
        canister = Canister.create(
            id=canister_id,
            label=label,
            canister_type_id=canister_type_id
        )
        logger.info(f"Created canister '{label}' with ID {canister.id}")
        return canister
    except Exception as e:
        logger.error(f"Error creating canister '{label}': {e}")
        raise
```

```python
# AFTER (class-based with transactions):
import peewee
from database_model import database, CanisterType, Canister, Weighing

class DatabaseManager:
    def __init__(self):
        self.database = database

    def read_single_canister(self, canister_id):
        """Retrieve a single canister by ID"""
        return Canister.get_or_none(Canister.id == canister_id)

    def read_all_canisters(self):
        """Retrieve all canisters"""
        return list(Canister.select())

    def write_canister(self, canister_data):
        """Create a new canister"""
        try:
            with database.atomic():
                Canister.create(**canister_data)
            return True, "Canister created successfully"
        except peewee.OperationalError as error:
            return False, f"Failed to create canister: {str(error)}"

    def update_canister_status(self, canister_id, new_status):
        """Update canister status"""
        try:
            with database.atomic():
                Canister.update(status=new_status).where(
                    Canister.id == canister_id
                ).execute()
            return True, f"Canister status updated to {new_status}"
        except peewee.OperationalError as error:
            return False, f"Failed to update status: {str(error)}"

    def delete_canister(self, canister_id):
        """Delete canister and its weighings"""
        try:
            with database.atomic():
                Weighing.delete().where(Weighing.canister_id == canister_id).execute()
                Canister.delete().where(Canister.id == canister_id).execute()
            return True, "Canister deleted successfully"
        except peewee.OperationalError as error:
            return False, f"Failed to delete canister: {str(error)}"
```

**Key changes:**
- ✅ Convert to DatabaseManager class
- ✅ Wrap all writes in `database.atomic()`
- ✅ Return `(bool, str)` tuples for write operations
- ✅ Use simple Peewee queries: `.get_or_none()`, `.select().where()`
- ✅ Keep logging but less verbose

**All methods:**
- `read_all_canister_types()`
- `read_canister_type_by_id(type_id)`
- `write_canister_type(type_data)`
- `delete_canister_type(type_id)`
- `read_all_canisters()`
- `read_single_canister(canister_id)`
- `write_canister(canister_data)`
- `update_canister_label(canister_id, new_label)`
- `update_canister_status(canister_id, status)`
- `delete_canister(canister_id)`
- `read_weighings_for_canister(canister_id)`
- `read_latest_weighing(canister_id)`
- `read_weighing_by_id(weighing_id)`
- `write_weighing(weighing_data)`
- `delete_weighing(weighing_id)`

---

### 4. ✨ CREATE business_logic.py (NEW)

```python
"""
Business logic layer for Gas Gauge application.
Handles calculations, orchestration, and data transformations.
"""

import logging
from datetime import datetime
from utils import generate_canister_id
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class BusinessLogic:
    def __init__(self):
        self.db_manager = DatabaseManager()

    # ========== Calculations ==========

    def calculate_gas_capacity(self, full_weight, empty_weight):
        """Calculate gas capacity from weights"""
        return full_weight - empty_weight

    def calculate_remaining_gas(self, weight, empty_weight):
        """Calculate remaining gas"""
        return weight - empty_weight

    def calculate_remaining_percentage(self, weight, empty_weight, gas_capacity):
        """Calculate remaining gas percentage"""
        if gas_capacity <= 0:
            return 0
        remaining_gas = weight - empty_weight
        percentage = (remaining_gas / gas_capacity) * 100
        return max(0, min(percentage, 100))

    def calculate_consumption_percentage(self, remaining_percentage):
        """Calculate consumption percentage"""
        return 100 - remaining_percentage

    def get_status_class(self, percentage):
        """Get CSS class for percentage"""
        if percentage is None:
            return "none"
        if percentage > 50:
            return "high"
        elif percentage > 25:
            return "medium"
        else:
            return "low"

    # ========== Orchestration ==========

    def get_dashboard_data(self):
        """Get all data for dashboard view"""
        canisters = self.db_manager.read_all_canisters()
        canister_types = self.db_manager.read_all_canister_types()

        canister_data = []
        for canister in canisters:
            # Get canister type
            canister_type = self.db_manager.read_canister_type_by_id(canister.canister_type_id)

            # Get latest weighing
            latest_weighing = self.db_manager.read_latest_weighing(canister.id)

            # Calculate percentage if weighing exists
            if latest_weighing and canister_type:
                gas_capacity = self.calculate_gas_capacity(
                    canister_type.full_weight,
                    canister_type.empty_weight
                )
                remaining_percentage = self.calculate_remaining_percentage(
                    latest_weighing.weight,
                    canister_type.empty_weight,
                    gas_capacity
                )
                status_class = self.get_status_class(remaining_percentage)
            else:
                remaining_percentage = None
                status_class = "none"

            canister_data.append({
                "canister": canister,
                "canister_type": canister_type,
                "latest_weighing": latest_weighing,
                "remaining_percentage": remaining_percentage,
                "status_class": status_class,
                "is_depleted": canister.status == "depleted"
            })

        # Sort: active first, then depleted
        canister_data.sort(key=lambda x: (x["is_depleted"], x["canister"]["label"]))

        suggested_label = generate_canister_id()[:7]

        return {
            "canisters": canister_data,
            "canister_types": canister_types,
            "suggested_label": suggested_label
        }

    def get_canister_detail_data(self, canister_id):
        """Get all data for canister detail view"""
        canister = self.db_manager.read_single_canister(canister_id)
        if not canister:
            return None

        canister_type = self.db_manager.read_canister_type_by_id(canister.canister_type_id)
        weighings_raw = self.db_manager.read_weighings_for_canister(canister_id)

        # Enrich weighings with calculations
        weighings = []
        for w in weighings_raw:
            gas_capacity = self.calculate_gas_capacity(
                canister_type.full_weight,
                canister_type.empty_weight
            )
            remaining_gas = self.calculate_remaining_gas(w.weight, canister_type.empty_weight)
            remaining_percentage = self.calculate_remaining_percentage(
                w.weight,
                canister_type.empty_weight,
                gas_capacity
            )
            consumption_percentage = self.calculate_consumption_percentage(remaining_percentage)

            weighings.append({
                "id": w.id,
                "weight": w.weight,
                "comment": w.comment,
                "recorded_at": w.recorded_at,
                "remaining_gas": remaining_gas,
                "remaining_percentage": remaining_percentage,
                "consumption_percentage": consumption_percentage
            })

        latest_weighing = weighings[0] if weighings else None
        status_class = self.get_status_class(
            latest_weighing["remaining_percentage"] if latest_weighing else None
        )

        return {
            "canister": canister,
            "canister_type": canister_type,
            "weighings": weighings,
            "latest_weighing": latest_weighing,
            "status_class": status_class
        }

    def create_canister(self, label, canister_type_id):
        """Create a new canister"""
        canister_id = generate_canister_id()
        canister_data = {
            "id": canister_id,
            "label": label.strip(),
            "canister_type_id": canister_type_id,
            "status": "active",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self.db_manager.write_canister(canister_data)

    def create_weighing(self, canister_id, weight, recorded_at_str, comment):
        """Create a new weighing record"""
        weighing_data = {
            "canister_id": canister_id,
            "weight": weight,
            "recorded_at": recorded_at_str,
            "comment": comment
        }
        return self.db_manager.write_weighing(weighing_data)

    def create_canister_type(self, name, full_weight, empty_weight):
        """Create a new canister type"""
        type_data = {
            "name": name,
            "full_weight": full_weight,
            "empty_weight": empty_weight
        }
        return self.db_manager.write_canister_type(type_data)
```

**Purpose:**
- ✅ All percentage calculations live here
- ✅ Orchestrates multi-table data fetching
- ✅ Enriches data for views
- ✅ Never calls database directly, only through db_manager

---

### 5. 🔨 REFACTOR main.py

**Consolidate all routes into single file:**

```python
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import init_db
from seed_data import seed_canister_types
from logger import setup_logging
from business_logic import BusinessLogic
import logging

# Setup logging
logger = setup_logging()

# Initialize app
app = FastAPI(title="Gas Gauge")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database
logger.info("Initializing database...")
init_db()
seed_canister_types()
logger.info("Database initialized")

# Initialize business logic
business_logic = BusinessLogic()

# ==================== HTML VIEWS ====================

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """Dashboard showing all canisters"""
    payload = business_logic.get_dashboard_data()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "canisters": payload["canisters"],
        "canister_types": payload["canister_types"],
        "suggested_label": payload["suggested_label"]
    })

@app.get("/canister/{canister_id}", response_class=HTMLResponse)
def canister_detail(request: Request, canister_id: str):
    """Canister detail page"""
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
        raise HTTPException(status_code=400, detail="Invalid label")

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
    return RedirectResponse(url="/", status_code=303)

@app.post("/canister/{canister_id}/reactivate")
def reactivate_canister(canister_id: str):
    """Reactivate depleted canister"""
    success, message = business_logic.db_manager.update_canister_status(
        canister_id, "active"
    )
    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@app.post("/canister/{canister_id}/delete")
def delete_canister_route(canister_id: str):
    """Delete canister and weighings"""
    success, message = business_logic.db_manager.delete_canister(canister_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/canister/{canister_id}/update-label")
def update_canister_label_route(
    canister_id: str,
    label: str = Form(...)
):
    """Update canister label"""
    if not label or len(label.strip()) == 0 or len(label) > 64:
        raise HTTPException(status_code=400, detail="Invalid label")

    success, message = business_logic.db_manager.update_canister_label(
        canister_id, label
    )
    return RedirectResponse(url=f"/canister/{canister_id}", status_code=303)

@app.post("/weighing/{weighing_id}/delete")
def delete_weighing_route(weighing_id: int):
    """Delete weighing record"""
    weighing = business_logic.db_manager.read_weighing_by_id(weighing_id)
    if weighing:
        canister_id = weighing.canister_id
        business_logic.db_manager.delete_weighing(weighing_id)
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
```

**Key changes:**
- ✅ All routes from routers/ consolidated here
- ✅ No Pydantic schemas, use Form(...) directly
- ✅ Manual validation where needed
- ✅ All routes call business_logic methods
- ✅ ~400 lines total

---

### 6. 📝 UPDATE seed_data.py

```python
import logging
from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

PREDEFINED_TYPES = [
    {"name": "Coleman 240g", "full_weight": 361, "empty_weight": 122},
]

def seed_canister_types():
    """Seed database with predefined canister types"""
    logger.info("Seeding predefined canister types...")
    db_manager = DatabaseManager()

    for type_data in PREDEFINED_TYPES:
        success, message = db_manager.write_canister_type(type_data)
        logger.info(message)

    logger.info("Canister type seeding complete.")
```

---

### 7. 📝 UPDATE database.py

```python
import os
from peewee import SqliteDatabase
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/gas_gauge.db")

# Ensure data directory exists
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

db = SqliteDatabase(DATABASE_PATH)

def init_db():
    """Initialize database tables"""
    from database_model import CanisterType, Canister, Weighing
    db.connect()
    db.create_tables([CanisterType, Canister, Weighing], safe=True)
    db.close()
```

**Changes:**
- ✅ Import from `database_model` instead of `models`

---

### 8. 📝 UPDATE templates (Minor fixes)

**templates/dashboard.html:**
- Line 134: Fix typo "Remaining Gas (% Wro)" → "Remaining Gas (%)"
- Update data access: `canister_data.canister` → `canister_data["canister"]`
- Update data access: `canister_data.latest_weighing` → `canister_data["latest_weighing"]`

**templates/canister_detail.html:**
- No major changes needed, but verify data structure matches new business_logic return format

---

## ✅ Validation Checklist

After refactoring, verify:

- [ ] App starts: `uvicorn main:app --reload --log-config uvicorn_log_config.ini`
- [ ] Dashboard loads at http://localhost:8000
- [ ] Can create new canister
- [ ] Can add weighing to canister
- [ ] Can view canister detail page
- [ ] Can mark canister as depleted
- [ ] Can reactivate canister
- [ ] Can delete weighing
- [ ] Can delete canister
- [ ] Admin types page works at http://localhost:8000/admin/types
- [ ] Can create new canister type
- [ ] Charts display correctly
- [ ] Show/hide depleted toggle works

---

## 📊 Before/After Comparison

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Python files | 22 | 7 | -68% |
| Router files | 4 | 0 (merged) | -100% |
| Test files | 8 | 0 | -100% |
| Total LOC | ~2,000 | ~1,200 | -40% |
| Dependencies | Peewee, Pydantic, FastAPI | Peewee, FastAPI | -1 |
| Complexity | Medium | Low | ✓ |

---

## 🎯 Benefits

**Simplicity:**
- ✅ Fewer files to navigate (22 → 7)
- ✅ Clear separation: data → database_manager → business_logic → routes
- ✅ No magic: explicit field types, explicit queries
- ✅ One file for all routes

**Maintainability:**
- ✅ All calculations in one place (business_logic.py)
- ✅ Consistent error handling (bool, str tuples)
- ✅ Transaction safety with database.atomic()
- ✅ Easier to understand data flow

**Performance:**
- ✅ Same performance as before
- ✅ Transactions prevent partial writes

---

## 🚨 Risks & Mitigations

**Risk:** Breaking existing database
- **Mitigation:** Models stay compatible, only code organization changes

**Risk:** Missing edge cases without tests
- **Mitigation:** Manual testing checklist above

**Risk:** Introducing bugs during refactor
- **Mitigation:** Execute methodically, one file at a time, verify app runs after each step

---

## 🏁 Execution Order

1. Create `database_model.py` (rename + simplify models.py)
2. Create `business_logic.py` (new file)
3. Refactor `database_manager.py` (convert to class)
4. Refactor `main.py` (consolidate routes)
5. Update `seed_data.py`
6. Update `database.py`
7. Delete `schemas.py`
8. Delete `routers/` folder
9. Delete `tests/` folder
10. Delete `recreate_db.py`
11. Fix template typos
12. Manual testing

---

## 📝 Notes

- Keep `utils.py`, `logger.py` unchanged
- Keep `requirements.txt` but can remove pytest dependencies later
- Keep Docker files unchanged
- Keep CLAUDE.md but update to reflect new structure
- Database file remains compatible (no schema migration needed)

---

**Ready to execute? Confirm to proceed with refactoring.**

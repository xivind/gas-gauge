# Gas Gauge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a web application to track gas remaining in camping stove canisters by recording weighings and calculating percentages.

**Architecture:** FastAPI backend with Jinja2 templates, Peewee ORM with SQLite database, Bootstrap + vanilla JS frontend with Chart.js visualizations, deployed via Docker.

**Tech Stack:** FastAPI, Uvicorn, Peewee, Jinja2, SQLite, Bootstrap 5, Chart.js, TomSelect, Docker

---

## Task 1: Project Dependencies and Structure

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`

**Step 1: Create requirements.txt**

Create `requirements.txt` with dependencies:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
peewee==3.17.0
jinja2==3.1.2
python-dotenv==1.0.0
pytest==7.4.3
```

**Step 2: Create environment example**

Create `.env.example`:

```
DATABASE_PATH=./data/gas_gauge.db
LOG_LEVEL=INFO
```

**Step 3: Create directory structure**

Run:
```bash
mkdir -p routers templates/admin static/css static/js data tests
```

**Step 4: Commit**

```bash
git add requirements.txt .env.example
git commit -m "feat: add project dependencies and structure"
```

---

## Task 2: Database Models

**Files:**
- Create: `models.py`
- Create: `database.py`

**Step 1: Write database connection**

Create `database.py`:

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
    from models import CanisterType, Canister, Weighing
    db.connect()
    db.create_tables([CanisterType, Canister, Weighing], safe=True)
    db.close()
```

**Step 2: Write models with tests**

Create `tests/test_models.py`:

```python
import pytest
from peewee import SqliteDatabase
from models import CanisterType, Canister, Weighing
from datetime import datetime

# Use in-memory database for tests
test_db = SqliteDatabase(':memory:')

@pytest.fixture
def setup_db():
    test_db.bind([CanisterType, Canister, Weighing])
    test_db.connect()
    test_db.create_tables([CanisterType, Canister, Weighing])
    yield
    test_db.drop_tables([CanisterType, Canister, Weighing])
    test_db.close()

def test_canister_type_gas_capacity(setup_db):
    canister_type = CanisterType.create(
        name="Coleman 240g",
        full_weight=361,
        empty_weight=122
    )
    assert canister_type.gas_capacity == 239

def test_weighing_remaining_gas(setup_db):
    canister_type = CanisterType.create(
        name="Coleman 240g",
        full_weight=361,
        empty_weight=122
    )
    canister = Canister.create(
        label="Gas Canister A",
        canister_type=canister_type,
        status="active"
    )
    weighing = Weighing.create(
        canister=canister,
        weight=324,
        comment="Test weighing"
    )
    assert weighing.remaining_gas == 202  # 324 - 122
    assert weighing.remaining_percentage == pytest.approx(84.5, 0.1)  # 202/239 * 100
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'models'"

**Step 4: Implement models**

Create `models.py`:

```python
from peewee import Model, CharField, IntegerField, ForeignKeyField, TextField, DateTimeField
from database import db
from datetime import datetime

class BaseModel(Model):
    class Meta:
        database = db

class CanisterType(BaseModel):
    name = CharField(unique=True)
    full_weight = IntegerField()  # grams
    empty_weight = IntegerField()  # grams

    @property
    def gas_capacity(self):
        return self.full_weight - self.empty_weight

class Canister(BaseModel):
    label = CharField()
    canister_type = ForeignKeyField(CanisterType, backref='canisters')
    status = CharField(default='active')  # active or depleted
    created_at = DateTimeField(default=datetime.now)

class Weighing(BaseModel):
    canister = ForeignKeyField(Canister, backref='weighings')
    weight = IntegerField()  # grams
    comment = TextField(null=True)
    recorded_at = DateTimeField(default=datetime.now)

    @property
    def remaining_gas(self):
        return self.weight - self.canister.canister_type.empty_weight

    @property
    def remaining_percentage(self):
        capacity = self.canister.canister_type.gas_capacity
        if capacity == 0:
            return 0
        return (self.remaining_gas / capacity) * 100

    @property
    def consumption_percentage(self):
        return 100 - self.remaining_percentage
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add models.py database.py tests/test_models.py
git commit -m "feat: add database models with computed properties"
```

---

## Task 3: Seed Data

**Files:**
- Create: `seed_data.py`

**Step 1: Write test for seed data**

Create `tests/test_seed_data.py`:

```python
import pytest
from peewee import SqliteDatabase
from models import CanisterType
from seed_data import seed_canister_types

test_db = SqliteDatabase(':memory:')

@pytest.fixture
def setup_db():
    test_db.bind([CanisterType])
    test_db.connect()
    test_db.create_tables([CanisterType])
    yield
    test_db.drop_tables([CanisterType])
    test_db.close()

def test_seed_canister_types(setup_db):
    seed_canister_types()
    types = list(CanisterType.select())
    assert len(types) >= 2
    coleman_240 = CanisterType.get(CanisterType.name == "Coleman 240g")
    assert coleman_240.full_weight == 361
    assert coleman_240.empty_weight == 122
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_seed_data.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'seed_data'"

**Step 3: Implement seed data**

Create `seed_data.py`:

```python
from models import CanisterType
import logging

logger = logging.getLogger(__name__)

PREDEFINED_TYPES = [
    {"name": "Coleman 240g", "full_weight": 361, "empty_weight": 122},
    {"name": "Coleman 450g", "full_weight": 600, "empty_weight": 200},
]

def seed_canister_types():
    """Seed database with predefined canister types"""
    for type_data in PREDEFINED_TYPES:
        canister_type, created = CanisterType.get_or_create(
            name=type_data["name"],
            defaults={
                "full_weight": type_data["full_weight"],
                "empty_weight": type_data["empty_weight"]
            }
        )
        if created:
            logger.info(f"Created canister type: {canister_type.name}")
        else:
            logger.debug(f"Canister type already exists: {canister_type.name}")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_seed_data.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add seed_data.py tests/test_seed_data.py
git commit -m "feat: add seed data for predefined canister types"
```

---

## Task 4: Logging Configuration

**Files:**
- Create: `logger.py`

**Step 1: Create logging configuration**

Create `logger.py`:

```python
import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def setup_logging():
    """Configure logging to output to stdout/stderr"""
    log_level = os.getenv("LOG_LEVEL", "INFO")

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)
```

**Step 2: Commit**

```bash
git add logger.py
git commit -m "feat: add logging configuration for console output"
```

---

## Task 5: Pydantic Schemas

**Files:**
- Create: `schemas.py`

**Step 1: Create Pydantic schemas**

Create `schemas.py`:

```python
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
```

**Step 2: Commit**

```bash
git add schemas.py
git commit -m "feat: add Pydantic schemas for request/response validation"
```

---

## Task 6: Canister Types Router

**Files:**
- Create: `routers/canister_types.py`
- Create: `tests/test_canister_types_router.py`

**Step 1: Write router test**

Create `tests/test_canister_types_router.py`:

```python
import pytest
from fastapi.testclient import TestClient
from peewee import SqliteDatabase
from models import CanisterType
from main import app

test_db = SqliteDatabase(':memory:')

@pytest.fixture
def setup_db():
    test_db.bind([CanisterType])
    test_db.connect()
    test_db.create_tables([CanisterType])
    yield
    test_db.drop_tables([CanisterType])
    test_db.close()

@pytest.fixture
def client():
    return TestClient(app)

def test_create_canister_type(setup_db, client):
    response = client.post("/api/canister-types", json={
        "name": "Test Type",
        "full_weight": 400,
        "empty_weight": 150
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Type"
    assert data["gas_capacity"] == 250

def test_list_canister_types(setup_db, client):
    CanisterType.create(name="Type 1", full_weight=400, empty_weight=150)
    CanisterType.create(name="Type 2", full_weight=600, empty_weight=200)

    response = client.get("/api/canister-types")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_canister_types_router.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'main'"

**Step 3: Implement router**

Create `routers/canister_types.py`:

```python
from fastapi import APIRouter, HTTPException
from models import CanisterType
from schemas import CanisterTypeCreate, CanisterTypeResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/canister-types", tags=["canister-types"])

@router.post("", response_model=CanisterTypeResponse)
def create_canister_type(canister_type: CanisterTypeCreate):
    """Create a new canister type"""
    try:
        ct = CanisterType.create(**canister_type.model_dump())
        logger.info(f"Created canister type: {ct.name}")
        return {
            "id": ct.id,
            "name": ct.name,
            "full_weight": ct.full_weight,
            "empty_weight": ct.empty_weight,
            "gas_capacity": ct.gas_capacity
        }
    except Exception as e:
        logger.error(f"Error creating canister type: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[CanisterTypeResponse])
def list_canister_types():
    """List all canister types"""
    types = CanisterType.select()
    return [{
        "id": ct.id,
        "name": ct.name,
        "full_weight": ct.full_weight,
        "empty_weight": ct.empty_weight,
        "gas_capacity": ct.gas_capacity
    } for ct in types]

@router.delete("/{type_id}")
def delete_canister_type(type_id: int):
    """Delete a canister type"""
    try:
        ct = CanisterType.get_by_id(type_id)
        ct.delete_instance()
        logger.info(f"Deleted canister type: {ct.name}")
        return {"success": True}
    except CanisterType.DoesNotExist:
        raise HTTPException(status_code=404, detail="Canister type not found")
```

**Step 4: Create minimal main.py to run tests**

Create `main.py`:

```python
from fastapi import FastAPI
from database import init_db
from logger import setup_logging
from routers import canister_types

# Setup logging
setup_logging()

# Initialize app
app = FastAPI(title="Gas Gauge")

# Initialize database
init_db()

# Include routers
app.include_router(canister_types.router)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_canister_types_router.py -v`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add routers/canister_types.py tests/test_canister_types_router.py main.py
git commit -m "feat: add canister types API router"
```

---

## Task 7: Canisters Router

**Files:**
- Create: `routers/canisters.py`
- Create: `tests/test_canisters_router.py`

**Step 1: Write router test**

Create `tests/test_canisters_router.py`:

```python
import pytest
from fastapi.testclient import TestClient
from peewee import SqliteDatabase
from models import CanisterType, Canister
from main import app

test_db = SqliteDatabase(':memory:')

@pytest.fixture
def setup_db():
    test_db.bind([CanisterType, Canister])
    test_db.connect()
    test_db.create_tables([CanisterType, Canister])
    yield
    test_db.drop_tables([CanisterType, Canister])
    test_db.close()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def canister_type(setup_db):
    return CanisterType.create(name="Coleman 240g", full_weight=361, empty_weight=122)

def test_create_canister(canister_type, client):
    response = client.post("/api/canisters", json={
        "label": "Gas Canister A",
        "canister_type_id": canister_type.id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "Gas Canister A"
    assert data["status"] == "active"

def test_list_active_canisters(canister_type, client):
    Canister.create(label="Canister 1", canister_type=canister_type, status="active")
    Canister.create(label="Canister 2", canister_type=canister_type, status="depleted")

    response = client.get("/api/canisters?status=active")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["label"] == "Canister 1"

def test_update_canister_status(canister_type, client):
    canister = Canister.create(label="Test", canister_type=canister_type, status="active")

    response = client.patch(f"/api/canisters/{canister.id}/status", json={"status": "depleted"})
    assert response.status_code == 200

    updated = Canister.get_by_id(canister.id)
    assert updated.status == "depleted"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_canisters_router.py -v`
Expected: FAIL with "404 Not Found" for /api/canisters

**Step 3: Implement router**

Create `routers/canisters.py`:

```python
from fastapi import APIRouter, HTTPException, Query
from models import Canister, CanisterType
from schemas import CanisterCreate, CanisterResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/canisters", tags=["canisters"])

@router.post("", response_model=CanisterResponse)
def create_canister(canister: CanisterCreate):
    """Create a new canister"""
    try:
        # Verify canister type exists
        CanisterType.get_by_id(canister.canister_type_id)

        c = Canister.create(**canister.model_dump())
        logger.info(f"Created canister: {c.label}")
        return {
            "id": c.id,
            "label": c.label,
            "canister_type_id": c.canister_type_id,
            "status": c.status,
            "created_at": c.created_at
        }
    except CanisterType.DoesNotExist:
        raise HTTPException(status_code=404, detail="Canister type not found")
    except Exception as e:
        logger.error(f"Error creating canister: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[CanisterResponse])
def list_canisters(status: Optional[str] = Query(None)):
    """List canisters, optionally filtered by status"""
    query = Canister.select()
    if status:
        query = query.where(Canister.status == status)

    return [{
        "id": c.id,
        "label": c.label,
        "canister_type_id": c.canister_type_id,
        "status": c.status,
        "created_at": c.created_at
    } for c in query]

@router.get("/{canister_id}", response_model=CanisterResponse)
def get_canister(canister_id: int):
    """Get a single canister by ID"""
    try:
        c = Canister.get_by_id(canister_id)
        return {
            "id": c.id,
            "label": c.label,
            "canister_type_id": c.canister_type_id,
            "status": c.status,
            "created_at": c.created_at
        }
    except Canister.DoesNotExist:
        raise HTTPException(status_code=404, detail="Canister not found")

@router.patch("/{canister_id}/status")
def update_canister_status(canister_id: int, status_update: dict):
    """Update canister status (active/depleted)"""
    try:
        c = Canister.get_by_id(canister_id)
        new_status = status_update.get("status")

        if new_status not in ["active", "depleted"]:
            raise HTTPException(status_code=400, detail="Invalid status")

        c.status = new_status
        c.save()
        logger.info(f"Updated canister {c.label} status to {new_status}")

        return {"success": True}
    except Canister.DoesNotExist:
        raise HTTPException(status_code=404, detail="Canister not found")
```

**Step 4: Update main.py to include router**

Update `main.py`:

```python
from fastapi import FastAPI
from database import init_db
from logger import setup_logging
from routers import canister_types, canisters

# Setup logging
setup_logging()

# Initialize app
app = FastAPI(title="Gas Gauge")

# Initialize database
init_db()

# Include routers
app.include_router(canister_types.router)
app.include_router(canisters.router)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_canisters_router.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add routers/canisters.py tests/test_canisters_router.py main.py
git commit -m "feat: add canisters API router"
```

---

## Task 8: Weighings Router

**Files:**
- Create: `routers/weighings.py`
- Create: `tests/test_weighings_router.py`

**Step 1: Write router test**

Create `tests/test_weighings_router.py`:

```python
import pytest
from fastapi.testclient import TestClient
from peewee import SqliteDatabase
from models import CanisterType, Canister, Weighing
from main import app

test_db = SqliteDatabase(':memory:')

@pytest.fixture
def setup_db():
    test_db.bind([CanisterType, Canister, Weighing])
    test_db.connect()
    test_db.create_tables([CanisterType, Canister, Weighing])
    yield
    test_db.drop_tables([CanisterType, Canister, Weighing])
    test_db.close()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def canister(setup_db):
    ct = CanisterType.create(name="Coleman 240g", full_weight=361, empty_weight=122)
    return Canister.create(label="Test Canister", canister_type=ct, status="active")

def test_create_weighing(canister, client):
    response = client.post("/api/weighings", json={
        "canister_id": canister.id,
        "weight": 324,
        "comment": "After weekend trip"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["weight"] == 324
    assert data["remaining_gas"] == 202
    assert data["comment"] == "After weekend trip"

def test_list_weighings_for_canister(canister, client):
    Weighing.create(canister=canister, weight=350, comment="First")
    Weighing.create(canister=canister, weight=300, comment="Second")

    response = client.get(f"/api/weighings?canister_id={canister.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_weighings_router.py -v`
Expected: FAIL with "404 Not Found" for /api/weighings

**Step 3: Implement router**

Create `routers/weighings.py`:

```python
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
        logger.info(f"Created weighing for canister {canister.label}: {w.weight}g")

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
def list_weighings(canister_id: Optional[int] = Query(None)):
    """List weighings, optionally filtered by canister"""
    query = Weighing.select()
    if canister_id:
        query = query.where(Weighing.canister == canister_id)

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
```

**Step 4: Update main.py to include router**

Update `main.py`:

```python
from fastapi import FastAPI
from database import init_db
from logger import setup_logging
from routers import canister_types, canisters, weighings

# Setup logging
setup_logging()

# Initialize app
app = FastAPI(title="Gas Gauge")

# Initialize database
init_db()

# Include routers
app.include_router(canister_types.router)
app.include_router(canisters.router)
app.include_router(weighings.router)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_weighings_router.py -v`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add routers/weighings.py tests/test_weighings_router.py main.py
git commit -m "feat: add weighings API router"
```

---

## Task 9: Base Template

**Files:**
- Create: `templates/base.html`

**Step 1: Create base template with Bootstrap and Chart.js**

Create `templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Gas Gauge{% endblock %}</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- TomSelect CSS -->
    <link href="https://cdn.jsdelivr.net/npm/tom-select@2.3.1/dist/css/tom-select.bootstrap5.css" rel="stylesheet">

    <!-- Custom CSS -->
    <link href="/static/css/custom.css" rel="stylesheet">

    {% block head %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">Gas Gauge</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/archive">Archive</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/admin/types">Canister Types</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <main class="container my-4">
        {% block content %}{% endblock %}
    </main>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

    <!-- TomSelect JS -->
    <script src="https://cdn.jsdelivr.net/npm/tom-select@2.3.1/dist/js/tom-select.complete.min.js"></script>

    <!-- Custom JS -->
    <script src="/static/js/app.js"></script>

    {% block scripts %}{% endblock %}
</body>
</html>
```

**Step 2: Commit**

```bash
git add templates/base.html
git commit -m "feat: add base template with Bootstrap, Chart.js, and TomSelect"
```

---

## Task 10: Custom CSS

**Files:**
- Create: `static/css/custom.css`

**Step 1: Create custom CSS with color coding**

Create `static/css/custom.css`:

```css
/* Canister card color coding */
.canister-card {
    transition: transform 0.2s;
    cursor: pointer;
}

.canister-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.percentage-display {
    font-size: 3rem;
    font-weight: bold;
}

.status-high {
    color: #28a745;
}

.status-medium {
    color: #ffc107;
}

.status-low {
    color: #dc3545;
}

.card-status-high {
    border-left: 5px solid #28a745;
}

.card-status-medium {
    border-left: 5px solid #ffc107;
}

.card-status-low {
    border-left: 5px solid #dc3545;
}

.card-depleted {
    opacity: 0.7;
    border-left: 5px solid #6c757d;
}

/* Chart containers */
.chart-container {
    position: relative;
    height: 300px;
    margin-bottom: 2rem;
}

/* Weighing history table */
.weighing-table {
    font-size: 0.9rem;
}

.weighing-table th {
    background-color: #f8f9fa;
}
```

**Step 2: Commit**

```bash
git add static/css/custom.css
git commit -m "feat: add custom CSS with color-coded status indicators"
```

---

## Task 11: Dashboard Page and View Router

**Files:**
- Create: `templates/dashboard.html`
- Create: `routers/views.py`
- Modify: `main.py`

**Step 1: Create dashboard template**

Create `templates/dashboard.html`:

```html
{% extends "base.html" %}

{% block title %}Dashboard - Gas Gauge{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Active Canisters</h1>
    <div>
        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addCanisterModal">
            Add New Canister
        </button>
        <a href="/archive" class="btn btn-secondary">View Archive</a>
    </div>
</div>

{% if canisters %}
<!-- Overview Chart -->
<div class="chart-container mb-4">
    <canvas id="overviewChart"></canvas>
</div>

<!-- Canister Cards -->
<div class="row">
    {% for canister_data in canisters %}
    <div class="col-md-4 mb-4">
        <div class="card canister-card card-status-{{ canister_data.status_class }}"
             onclick="window.location.href='/canister/{{ canister_data.canister.id }}'">
            <div class="card-body">
                <h5 class="card-title">{{ canister_data.canister.label }}</h5>
                <p class="card-text text-muted">{{ canister_data.canister.canister_type.name }}</p>

                {% if canister_data.latest_weighing %}
                <div class="percentage-display status-{{ canister_data.status_class }}">
                    {{ "%.0f"|format(canister_data.latest_weighing.remaining_percentage) }}%
                </div>
                <p class="card-text">
                    <small class="text-muted">
                        Last weighed: {{ canister_data.latest_weighing.recorded_at.strftime('%Y-%m-%d') }}
                    </small>
                </p>
                {% else %}
                <p class="card-text text-muted">No weighings yet</p>
                {% endif %}
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="alert alert-info">
    No active canisters. Click "Add New Canister" to get started.
</div>
{% endif %}

<!-- Add Canister Modal -->
<div class="modal fade" id="addCanisterModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add New Canister</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST" action="/canister/create">
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="label" class="form-label">Canister Label</label>
                        <input type="text" class="form-control" id="label" name="label" required>
                    </div>
                    <div class="mb-3">
                        <label for="canister_type_id" class="form-label">Canister Type</label>
                        <select class="form-select" id="canister_type_id" name="canister_type_id" required>
                            {% for ct in canister_types %}
                            <option value="{{ ct.id }}">{{ ct.name }} ({{ ct.gas_capacity }}g capacity)</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Add Canister</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="/static/js/charts.js"></script>
<script>
    // Initialize TomSelect for canister type dropdown
    new TomSelect('#canister_type_id', {
        placeholder: 'Select canister type...',
    });

    // Create overview chart
    const chartData = {
        labels: [{% for cd in canisters %}'{{ cd.canister.label }}',{% endfor %}],
        datasets: [{
            label: 'Remaining Gas (%)',
            data: [{% for cd in canisters %}{{ cd.latest_weighing.remaining_percentage if cd.latest_weighing else 0 }},{% endfor %}],
            backgroundColor: [{% for cd in canisters %}
                '{% if cd.status_class == "high" %}rgba(40, 167, 69, 0.7){% elif cd.status_class == "medium" %}rgba(255, 193, 7, 0.7){% else %}rgba(220, 53, 69, 0.7){% endif %}',
            {% endfor %}]
        }]
    };

    createBarChart('overviewChart', chartData, 'Active Canisters Overview');
</script>
{% endblock %}
```

**Step 2: Create views router**

Create `routers/views.py`:

```python
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
```

**Step 3: Update main.py to include Jinja2 and static files**

Update `main.py`:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import init_db
from seed_data import seed_canister_types
from logger import setup_logging
from routers import canister_types, canisters, weighings, views
import logging

# Setup logging
logger = setup_logging()

# Initialize app
app = FastAPI(title="Gas Gauge")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize database
logger.info("Initializing database...")
init_db()
seed_canister_types()
logger.info("Database initialized")

# Include routers
app.include_router(canister_types.router)
app.include_router(canisters.router)
app.include_router(weighings.router)
app.include_router(views.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Step 4: Commit**

```bash
git add templates/dashboard.html routers/views.py main.py
git commit -m "feat: add dashboard view with canister cards and overview chart"
```

---

## Task 12: Charts JavaScript

**Files:**
- Create: `static/js/charts.js`

**Step 1: Create Chart.js helper functions**

Create `static/js/charts.js`:

```javascript
/**
 * Create a bar chart
 */
function createBarChart(canvasId, data, title) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: title
                },
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Create a line chart for gas remaining over time
 */
function createLineChart(canvasId, data, title) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: title
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Create a consumption bar chart
 */
function createConsumptionChart(canvasId, data, title) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: title
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            return context.raw.comment || '';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}
```

**Step 2: Commit**

```bash
git add static/js/charts.js
git commit -m "feat: add Chart.js helper functions for visualizations"
```

---

## Task 13: App JavaScript

**Files:**
- Create: `static/js/app.js`

**Step 1: Create app JavaScript for form handling**

Create `static/js/app.js`:

```javascript
/**
 * Handle form submissions and interactions
 */

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });
});

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Format number to fixed decimals
 */
function formatNumber(num, decimals = 1) {
    return Number(num).toFixed(decimals);
}
```

**Step 2: Commit**

```bash
git add static/js/app.js
git commit -m "feat: add app JavaScript for form handling and utilities"
```

---

## Task 14: Canister Detail Page

**Files:**
- Create: `templates/canister_detail.html`
- Modify: `routers/views.py`

**Step 1: Create canister detail template**

Create `templates/canister_detail.html`:

```html
{% extends "base.html" %}

{% block title %}{{ canister.label }} - Gas Gauge{% endblock %}

{% block content %}
<div class="mb-4">
    <a href="/" class="btn btn-sm btn-secondary">&larr; Back to Dashboard</a>
</div>

<div class="row mb-4">
    <div class="col-md-8">
        <h1>{{ canister.label }}</h1>
        <p class="text-muted">{{ canister.canister_type.name }}</p>
    </div>
    <div class="col-md-4 text-end">
        {% if latest_weighing %}
        <div class="percentage-display status-{{ status_class }}">
            {{ "%.0f"|format(latest_weighing.remaining_percentage) }}%
        </div>
        <p class="text-muted">{{ latest_weighing.remaining_gas }}g / {{ canister.canister_type.gas_capacity }}g</p>
        {% endif %}
    </div>
</div>

<div class="mb-4">
    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addWeighingModal">
        Add Weighing
    </button>
    {% if canister.status == "active" %}
    <form method="POST" action="/canister/{{ canister.id }}/mark-depleted" style="display: inline;">
        <button type="submit" class="btn btn-warning" onclick="return confirm('Mark this canister as depleted?')">
            Mark as Depleted
        </button>
    </form>
    {% else %}
    <form method="POST" action="/canister/{{ canister.id }}/reactivate" style="display: inline;">
        <button type="submit" class="btn btn-success">
            Reactivate
        </button>
    </form>
    {% endif %}
</div>

{% if weighings %}
<!-- Charts -->
<div class="row mb-4">
    <div class="col-md-12">
        <div class="chart-container">
            <canvas id="gasOverTimeChart"></canvas>
        </div>
    </div>
</div>

<!-- Weighing History Table -->
<h3>Weighing History</h3>
<table class="table table-striped weighing-table">
    <thead>
        <tr>
            <th>Date</th>
            <th>Weight (g)</th>
            <th>Remaining Gas (g)</th>
            <th>Remaining (%)</th>
            <th>Consumption (%)</th>
            <th>Comment</th>
        </tr>
    </thead>
    <tbody>
        {% for weighing in weighings %}
        <tr>
            <td>{{ weighing.recorded_at.strftime('%Y-%m-%d %H:%M') }}</td>
            <td>{{ weighing.weight }}</td>
            <td>{{ weighing.remaining_gas }}</td>
            <td>{{ "%.1f"|format(weighing.remaining_percentage) }}%</td>
            <td>{{ "%.1f"|format(weighing.consumption_percentage) }}%</td>
            <td>{{ weighing.comment or '-' }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<div class="alert alert-info">
    No weighings recorded yet. Click "Add Weighing" to get started.
</div>
{% endif %}

<!-- Add Weighing Modal -->
<div class="modal fade" id="addWeighingModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add Weighing</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST" action="/canister/{{ canister.id }}/add-weighing">
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="weight" class="form-label">Weight (grams)</label>
                        <input type="number" class="form-control" id="weight" name="weight" required min="1">
                        <small class="text-muted">Full weight: {{ canister.canister_type.full_weight }}g</small>
                    </div>
                    <div class="mb-3">
                        <label for="comment" class="form-label">Comment (optional)</label>
                        <textarea class="form-control" id="comment" name="comment" rows="3"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Add Weighing</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="/static/js/charts.js"></script>
<script>
    // Create gas over time chart
    const chartData = {
        labels: [{% for w in weighings|reverse %}'{{ w.recorded_at.strftime('%Y-%m-%d') }}',{% endfor %}],
        datasets: [{
            label: 'Remaining Gas (g)',
            data: [{% for w in weighings|reverse %}{{ w.remaining_gas }},{% endfor %}],
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            tension: 0.1
        }]
    };

    createLineChart('gasOverTimeChart', chartData, 'Gas Remaining Over Time');
</script>
{% endblock %}
```

**Step 2: Add routes to views.py**

Add to `routers/views.py`:

```python
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
```

**Step 3: Commit**

```bash
git add templates/canister_detail.html routers/views.py
git commit -m "feat: add canister detail page with weighing history and charts"
```

---

## Task 15: Archive Page

**Files:**
- Create: `templates/archive.html`
- Modify: `routers/views.py`

**Step 1: Create archive template**

Create `templates/archive.html`:

```html
{% extends "base.html" %}

{% block title %}Archive - Gas Gauge{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Depleted Canisters Archive</h1>
    <a href="/" class="btn btn-secondary">Back to Dashboard</a>
</div>

{% if canisters %}
<div class="row">
    {% for canister_data in canisters %}
    <div class="col-md-4 mb-4">
        <div class="card canister-card card-depleted"
             onclick="window.location.href='/canister/{{ canister_data.canister.id }}'">
            <div class="card-body">
                <h5 class="card-title">{{ canister_data.canister.label }}</h5>
                <p class="card-text text-muted">{{ canister_data.canister.canister_type.name }}</p>

                {% if canister_data.latest_weighing %}
                <div class="text-muted">
                    <p class="mb-1">Final weight: {{ canister_data.latest_weighing.weight }}g</p>
                    <p class="mb-1">
                        <small>
                            Depleted on: {{ canister_data.latest_weighing.recorded_at.strftime('%Y-%m-%d') }}
                        </small>
                    </p>
                </div>
                {% endif %}

                <p class="card-text">
                    <small class="text-muted">
                        Total weighings: {{ canister_data.weighing_count }}
                    </small>
                </p>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="alert alert-info">
    No depleted canisters in archive.
</div>
{% endif %}
{% endblock %}
```

**Step 2: Add route to views.py**

Add to `routers/views.py`:

```python
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
```

**Step 3: Commit**

```bash
git add templates/archive.html routers/views.py
git commit -m "feat: add archive page for depleted canisters"
```

---

## Task 16: Admin Types Page

**Files:**
- Create: `templates/admin/types.html`
- Modify: `routers/views.py`

**Step 1: Create admin types template**

Create `templates/admin/types.html`:

```html
{% extends "base.html" %}

{% block title %}Canister Types - Gas Gauge{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Canister Types</h1>
    <div>
        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addTypeModal">
            Add New Type
        </button>
        <a href="/" class="btn btn-secondary">Back to Dashboard</a>
    </div>
</div>

<table class="table table-striped">
    <thead>
        <tr>
            <th>Name</th>
            <th>Full Weight (g)</th>
            <th>Empty Weight (g)</th>
            <th>Gas Capacity (g)</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for ct in canister_types %}
        <tr>
            <td>{{ ct.name }}</td>
            <td>{{ ct.full_weight }}</td>
            <td>{{ ct.empty_weight }}</td>
            <td>{{ ct.gas_capacity }}</td>
            <td>
                {% if ct.name not in ['Coleman 240g', 'Coleman 450g'] %}
                <form method="POST" action="/admin/types/{{ ct.id }}/delete" style="display: inline;">
                    <button type="submit" class="btn btn-sm btn-danger"
                            onclick="return confirm('Delete this canister type?')">
                        Delete
                    </button>
                </form>
                {% else %}
                <span class="badge bg-secondary">Built-in</span>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<!-- Add Type Modal -->
<div class="modal fade" id="addTypeModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add Canister Type</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST" action="/admin/types/create">
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="name" class="form-label">Name</label>
                        <input type="text" class="form-control" id="name" name="name" required>
                    </div>
                    <div class="mb-3">
                        <label for="full_weight" class="form-label">Full Weight (grams)</label>
                        <input type="number" class="form-control" id="full_weight" name="full_weight" required min="1">
                    </div>
                    <div class="mb-3">
                        <label for="empty_weight" class="form-label">Empty Weight (grams)</label>
                        <input type="number" class="form-control" id="empty_weight" name="empty_weight" required min="1">
                    </div>
                    <div class="alert alert-info">
                        <strong>Gas Capacity:</strong> <span id="capacity">-</span>g
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Add Type</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    // Calculate capacity dynamically
    const fullWeightInput = document.getElementById('full_weight');
    const emptyWeightInput = document.getElementById('empty_weight');
    const capacityDisplay = document.getElementById('capacity');

    function updateCapacity() {
        const full = parseInt(fullWeightInput.value) || 0;
        const empty = parseInt(emptyWeightInput.value) || 0;
        capacityDisplay.textContent = Math.max(0, full - empty);
    }

    fullWeightInput.addEventListener('input', updateCapacity);
    emptyWeightInput.addEventListener('input', updateCapacity);
</script>
{% endblock %}
```

**Step 2: Add routes to views.py**

Add to `routers/views.py`:

```python
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
```

**Step 3: Commit**

```bash
git add templates/admin/types.html routers/views.py
git commit -m "feat: add admin page for managing canister types"
```

---

## Task 17: Dockerfile

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

**Step 1: Create Dockerfile**

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Create .dockerignore**

Create `.dockerignore`:

```
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
.coverage
htmlcov
.env
*.db
data/
.git
.gitignore
*.md
tests/
.worktrees/
```

**Step 3: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "feat: add Dockerfile for containerized deployment"
```

---

## Task 18: README Documentation

**Files:**
- Modify: `README.md`

**Step 1: Update README with comprehensive documentation**

Update `README.md`:

```markdown
# Gas Gauge

A web application to track remaining gas in canisters for camp stoves.

![Dashboard Screenshot](docs/screenshot.png)

## Features

- **Dashboard**: View all active canisters with remaining gas percentages
- **Weighing History**: Track multiple weighings per canister over time
- **Visual Analytics**: Charts showing gas consumption trends
- **Archive**: Keep history of depleted canisters
- **Custom Types**: Add your own canister types
- **Color-coded Status**: Quick visual identification of canister levels
  - Green: >50% remaining
  - Yellow: 25-50% remaining
  - Red: <25% remaining

## Quick Start

### Using Docker

1. **Build the image:**
   ```bash
   docker build -t gas-gauge .
   ```

2. **Run the container:**
   ```bash
   docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --name gas-gauge gas-gauge
   ```

3. **Open your browser:**
   Navigate to `http://localhost:8000`

### View Logs

```bash
docker logs -f gas-gauge
```

### Stop/Start

```bash
docker stop gas-gauge
docker start gas-gauge
```

### Remove Container

```bash
docker stop gas-gauge
docker rm gas-gauge
```

## Database Backup

Your data is stored in `./data/gas_gauge.db`. To backup:

```bash
cp -r ./data ./data-backup-$(date +%Y%m%d)
```

## Development

### Local Setup (without Docker)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   uvicorn main:app --reload
   ```

3. **Run tests:**
   ```bash
   pytest
   ```

### Project Structure

```
gas-gauge/
├── main.py              # FastAPI app initialization
├── models.py            # Database models
├── database.py          # Database connection
├── schemas.py           # Pydantic schemas
├── seed_data.py         # Seed predefined canister types
├── logger.py            # Logging configuration
├── routers/             # API and view routes
├── templates/           # Jinja2 templates
├── static/              # CSS and JavaScript
├── tests/               # Test suite
└── data/                # SQLite database (created at runtime)
```

## Usage Guide

### Adding a Canister

1. Click "Add New Canister" on the dashboard
2. Enter a label (e.g., "Gas Canister A")
3. Select canister type
4. Click "Add Canister"

### Recording a Weighing

1. Click on a canister card
2. Click "Add Weighing"
3. Enter weight in grams
4. Optionally add a comment about the trip
5. Click "Add Weighing"

### Marking as Depleted

1. Go to canister detail page
2. Click "Mark as Depleted"
3. Canister moves to archive but retains all history

### Adding Custom Canister Types

1. Navigate to "Canister Types" in the menu
2. Click "Add New Type"
3. Enter name, full weight, and empty weight
4. Gas capacity is calculated automatically

## Tech Stack

- **Backend:** FastAPI, Peewee ORM, SQLite
- **Frontend:** Bootstrap 5, Chart.js, TomSelect, Vanilla JavaScript
- **Templates:** Jinja2
- **Deployment:** Docker

## License

MIT License - feel free to clone and run your own instance!
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README with usage guide"
```

---

## Task 19: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update CLAUDE.md with project details**

Update `CLAUDE.md`:

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gas Gauge is a web application to track remaining gas in canisters for camp stoves. Users weigh canisters after trips, record weights with comments, and view remaining gas percentages to choose appropriate canisters for upcoming trips.

## Technology Stack

- **Backend:** FastAPI, Uvicorn, Peewee ORM, SQLite
- **Frontend:** Jinja2 templates, Bootstrap 5, Chart.js, TomSelect, Vanilla JavaScript
- **Deployment:** Docker (no docker-compose)
- **Testing:** pytest

## Development Commands

### Running the App

**With Docker (recommended):**
```bash
# Build
docker build -t gas-gauge .

# Run
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --name gas-gauge gas-gauge

# View logs
docker logs -f gas-gauge

# Stop/Start
docker stop gas-gauge
docker start gas-gauge
```

**Without Docker:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn main:app --reload

# Run for production
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Architecture

### Database Models

Three main models with computed properties:

1. **CanisterType**: Predefined specifications (Coleman 240g, etc.)
   - Stores: name, full_weight, empty_weight
   - Computes: gas_capacity

2. **Canister**: Individual physical canisters
   - Stores: label, type reference, status (active/depleted)
   - Has many: weighings

3. **Weighing**: Weight recordings over time
   - Stores: weight, comment, timestamp
   - Computes: remaining_gas, remaining_percentage, consumption_percentage

### Router Structure

- `routers/canister_types.py`: API for managing canister types
- `routers/canisters.py`: API for canister CRUD
- `routers/weighings.py`: API for recording weighings
- `routers/views.py`: HTML views (dashboard, detail, archive, admin)

### Frontend Organization

- `templates/base.html`: Base template with Bootstrap, Chart.js, TomSelect
- `templates/dashboard.html`: Active canisters with overview chart
- `templates/canister_detail.html`: Individual canister with history and charts
- `templates/archive.html`: Depleted canisters
- `templates/admin/types.html`: Manage canister types
- `static/css/custom.css`: Color-coded status indicators
- `static/js/charts.js`: Chart.js helper functions
- `static/js/app.js`: Form handling and utilities

### Color Coding Logic

Status classes based on remaining percentage:
- **high** (green): > 50%
- **medium** (yellow): 25-50%
- **low** (red): < 25%

Implemented in `routers/views.py::get_status_class()`

### Logging

All logs output to stdout/stderr for Docker visibility:
- Configured in `logger.py`
- View with: `docker logs -f gas-gauge`
- Logs: startup, requests, weighing additions, errors

## Database Management

### Location
- Development: `./data/gas_gauge.db`
- Docker: Persisted via volume mount `-v $(pwd)/data:/app/data`

### Initialization
- Tables created automatically on first run
- Seed data (Coleman types) populated by `seed_data.py`

### Backup
```bash
cp -r ./data ./data-backup-$(date +%Y%m%d)
```

## Key Design Decisions

1. **Single-user per instance**: No authentication, simpler deployment
2. **SQLite**: Lightweight, file-based, easy backup
3. **Computed properties**: Percentages calculated on-the-fly from model methods
4. **No soft deletes**: Depleted status preserves history without deletion
5. **Vanilla JS**: No build step, keep frontend simple
6. **TomSelect for dropdowns**: Better UX than plain select elements
7. **Chart.js**: Visualize trends without heavy dependencies

## Worktree Configuration

Worktrees should be created in `.worktrees/` (already in .gitignore).

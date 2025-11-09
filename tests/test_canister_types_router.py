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

import pytest
from models import CanisterType

def test_create_canister_type(client):
    response = client.post("/api/canister-types", json={
        "name": "Test Type",
        "full_weight": 400,
        "empty_weight": 150
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Type"
    assert data["gas_capacity"] == 250

def test_list_canister_types(client):
    CanisterType.create(name="Type 1", full_weight=400, empty_weight=150)
    CanisterType.create(name="Type 2", full_weight=600, empty_weight=200)

    response = client.get("/api/canister-types")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

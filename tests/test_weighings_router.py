import pytest
from models import Weighing

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

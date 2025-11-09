import pytest
from models import CanisterType, Canister

@pytest.fixture
def canister_type():
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

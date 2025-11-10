import pytest


def test_create_canister(client):
    # First create a canister type
    type_response = client.post("/api/canister-types", json={
        "name": "Test Type",
        "full_weight": 400,
        "empty_weight": 100
    })
    type_id = type_response.json()["id"]

    # Create canister with label
    response = client.post("/api/canisters", json={
        "label": "My Coleman Canister",
        "canister_type_id": type_id
    })

    assert response.status_code == 200
    data = response.json()

    # ID should be string with correct format
    assert isinstance(data["id"], str)
    assert data["id"].startswith("GC-")
    assert len(data["id"]) == 13

    # Label should match
    assert data["label"] == "My Coleman Canister"


def test_create_canister_empty_label(client):
    """Test that empty label is rejected"""
    type_response = client.post("/api/canister-types", json={
        "name": "Test Type",
        "full_weight": 400,
        "empty_weight": 100
    })
    type_id = type_response.json()["id"]

    response = client.post("/api/canisters", json={
        "label": "",
        "canister_type_id": type_id
    })

    # Pydantic validation returns 422 for validation errors
    assert response.status_code == 422


def test_create_canister_label_too_long(client):
    """Test that label exceeding 64 chars is rejected"""
    type_response = client.post("/api/canister-types", json={
        "name": "Test Type",
        "full_weight": 400,
        "empty_weight": 100
    })
    type_id = type_response.json()["id"]

    response = client.post("/api/canisters", json={
        "label": "X" * 65,
        "canister_type_id": type_id
    })

    # Pydantic validation returns 422 for validation errors
    assert response.status_code == 422


def test_list_active_canisters(client, canister):
    response = client.get("/api/canisters?status=active")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    # Verify ID is string
    assert isinstance(data[0]["id"], str)


def test_update_canister_status(client, canister):
    response = client.patch(f"/api/canisters/{canister.id}/status", json={
        "status": "depleted"
    })
    assert response.status_code == 200

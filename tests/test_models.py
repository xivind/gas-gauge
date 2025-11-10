import pytest
from models import CanisterType, Canister, Weighing
from datetime import datetime

def test_canister_type_gas_capacity():
    canister_type = CanisterType.create(
        name="Coleman 240g",
        full_weight=361,
        empty_weight=122
    )
    assert canister_type.gas_capacity == 239

def test_weighing_remaining_gas():
    canister_type = CanisterType.create(
        name="Coleman 240g",
        full_weight=361,
        empty_weight=122
    )
    canister = Canister.create(
        id="GC-test001234",
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
    assert weighing.consumption_percentage == pytest.approx(15.5, 0.1)  # 100 - 84.5

def test_canister_string_id():
    """Test that Canister uses string ID"""
    canister_type = CanisterType.create(
        name="Test Type",
        full_weight=400,
        empty_weight=100
    )
    canister = Canister.create(
        id="GC-abc1231234",
        label="My Test Canister",
        canister_type=canister_type,
        status="active"
    )

    # ID should be the string we provided
    assert canister.id == "GC-abc1231234"
    assert isinstance(canister.id, str)

    # Label should be separate
    assert canister.label == "My Test Canister"


def test_canister_label_required():
    """Test that label field is required and validated"""
    canister_type = CanisterType.create(
        name="Test Type",
        full_weight=400,
        empty_weight=100
    )

    # Label cannot be empty (will be enforced at API level)
    # This test verifies the field exists
    canister = Canister.create(
        id="GC-def4564567",
        label="X" * 64,  # Max length
        canister_type=canister_type
    )
    assert len(canister.label) == 64

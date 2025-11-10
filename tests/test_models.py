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

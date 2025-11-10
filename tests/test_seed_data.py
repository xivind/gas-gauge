import pytest
from models import CanisterType
from seed_data import seed_canister_types

def test_seed_canister_types():
    seed_canister_types()
    types = list(CanisterType.select())
    assert len(types) >= 2
    coleman_240 = CanisterType.get(CanisterType.name == "Coleman 240g")
    assert coleman_240.full_weight == 361
    assert coleman_240.empty_weight == 122

def test_seed_canister_types_idempotent():
    """Test that seed_canister_types can run multiple times without creating duplicates"""
    # First run of seed
    seed_canister_types()
    types_after_first_run = list(CanisterType.select())
    count_after_first_run = len(types_after_first_run)

    # Verify Coleman 240g exists with correct values
    coleman_240 = CanisterType.get(CanisterType.name == "Coleman 240g")
    assert coleman_240.full_weight == 361
    assert coleman_240.empty_weight == 122

    # Second run of seed
    seed_canister_types()
    types_after_second_run = list(CanisterType.select())
    count_after_second_run = len(types_after_second_run)

    # Verify count is the same (no duplicates)
    assert count_after_first_run == count_after_second_run

    # Verify Coleman 240g still has correct values
    coleman_240_after = CanisterType.get(CanisterType.name == "Coleman 240g")
    assert coleman_240_after.full_weight == 361
    assert coleman_240_after.empty_weight == 122

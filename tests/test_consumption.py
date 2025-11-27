import pytest
from unittest.mock import MagicMock
from business_logic import BusinessLogic

class MockWeighing:
    def __init__(self, id, weight, recorded_at, comment=""):
        self.id = id
        self.weight = weight
        self.recorded_at = recorded_at
        self.comment = comment
        self.canister_id = "test_canister"

class MockCanisterType:
    def __init__(self, full_weight, empty_weight):
        self.full_weight = full_weight
        self.empty_weight = empty_weight

class MockCanister:
    def __init__(self, id, canister_type_id):
        self.id = id
        self.canister_type_id = canister_type_id
        self.label = "Test Canister"
        self.status = "active"

def test_consumption_calculation():
    # Setup
    logic = BusinessLogic()
    logic.db_manager = MagicMock()

    # Data
    # Type: 100g full, 0g empty -> 100g capacity
    canister_type = MockCanisterType(100, 0)
    canister = MockCanister("c1", 1)
    
    # Weighings (newest to oldest)
    # 1. 50g remaining (50%) -> Consumption should be 30% (80% - 50%)
    # 2. 80g remaining (80%) -> Consumption should be 10% (90% - 80%)
    # 3. 90g remaining (90%) -> Consumption should be 10% (100% - 90%)
    weighings = [
        MockWeighing(3, 50, "2023-01-03"),
        MockWeighing(2, 80, "2023-01-02"),
        MockWeighing(1, 90, "2023-01-01"),
    ]

    # Mocks
    logic.db_manager.read_single_canister.return_value = canister
    logic.db_manager.read_canister_type_by_id.return_value = canister_type
    logic.db_manager.read_weighings_for_canister.return_value = weighings

    # Execute
    data = logic.get_canister_detail_data("c1")
    
    # Verify
    results = data["weighings"]
    
    # Check oldest (index 2)
    # 90g remaining = 90%. Consumption = 100 - 90 = 10%
    assert results[2]["consumption_percentage"] == 10.0
    
    # Check middle (index 1)
    # 80g remaining = 80%. Previous was 90%. Consumption = 90 - 80 = 10%
    assert results[1]["consumption_percentage"] == 10.0
    
    # Check newest (index 0)
    # 50g remaining = 50%. Previous was 80%. Consumption = 80 - 50 = 30%
    assert results[0]["consumption_percentage"] == 30.0

def test_consumption_calculation_single_record():
    # Setup
    logic = BusinessLogic()
    logic.db_manager = MagicMock()
    
    canister_type = MockCanisterType(100, 0)
    canister = MockCanister("c1", 1)
    
    # 1. 90g remaining (90%) -> Consumption should be 10%
    weighings = [
        MockWeighing(1, 90, "2023-01-01"),
    ]

    logic.db_manager.read_single_canister.return_value = canister
    logic.db_manager.read_canister_type_by_id.return_value = canister_type
    logic.db_manager.read_weighings_for_canister.return_value = weighings

    data = logic.get_canister_detail_data("c1")
    results = data["weighings"]
    
    assert results[0]["consumption_percentage"] == 10.0

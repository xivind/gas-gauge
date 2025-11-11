import pytest
from models import Canister, CanisterType, Weighing
from database import db
from datetime import datetime, timedelta


@pytest.fixture
def setup_test_db():
    """Setup test database"""
    db.connect()
    db.create_tables([CanisterType, Canister, Weighing], safe=True)
    yield
    db.drop_tables([Weighing, Canister, CanisterType], safe=True)
    db.close()


def test_multiple_weighings_per_canister(setup_test_db):
    """Test that multiple weighings can be created for the same canister"""
    # Create canister type
    ct = CanisterType.create(
        name="Test Type",
        full_weight=350,
        empty_weight=110
    )

    # Create canister
    canister = Canister.create(
        id="GC-test123456",
        label="Test Canister",
        canister_type=ct
    )

    # Create multiple weighings
    weighing1 = Weighing.create(
        canister=canister,
        weight=350,
        recorded_at=datetime.now() - timedelta(days=2),
        comment="First weighing"
    )

    weighing2 = Weighing.create(
        canister=canister,
        weight=300,
        recorded_at=datetime.now() - timedelta(days=1),
        comment="Second weighing"
    )

    weighing3 = Weighing.create(
        canister=canister,
        weight=250,
        recorded_at=datetime.now(),
        comment="Third weighing"
    )

    # Verify all weighings exist
    all_weighings = list(Weighing.select().where(Weighing.canister == canister))
    assert len(all_weighings) == 3, f"Expected 3 weighings, got {len(all_weighings)}"

    # Verify they have different IDs
    ids = [w.id for w in all_weighings]
    assert len(set(ids)) == 3, "Weighings should have unique IDs"

    # Verify the weights are correct
    weights = sorted([w.weight for w in all_weighings])
    assert weights == [250, 300, 350], f"Expected weights [250, 300, 350], got {weights}"

    print(f"✓ Successfully created {len(all_weighings)} weighings for canister {canister.label}")
    print(f"  Weighing IDs: {ids}")
    print(f"  Weights: {weights}")


def test_weighing_with_canister_id_parameter(setup_test_db):
    """Test creating weighing using canister_id parameter (old method)"""
    # Create canister type
    ct = CanisterType.create(
        name="Test Type 2",
        full_weight=450,
        empty_weight=150
    )

    # Create canister
    canister = Canister.create(
        id="GC-test789012",
        label="Test Canister 2",
        canister_type=ct
    )

    # Create weighings using canister_id (the old way)
    weighing1 = Weighing.create(
        canister_id=canister.id,
        weight=400,
        recorded_at=datetime.now() - timedelta(days=1)
    )

    weighing2 = Weighing.create(
        canister_id=canister.id,
        weight=350,
        recorded_at=datetime.now()
    )

    # Verify both weighings exist
    all_weighings = list(Weighing.select().where(Weighing.canister == canister))
    assert len(all_weighings) == 2, f"Expected 2 weighings, got {len(all_weighings)}"

    print(f"✓ Successfully created {len(all_weighings)} weighings using canister_id parameter")

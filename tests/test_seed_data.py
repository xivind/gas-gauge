import pytest
from peewee import SqliteDatabase
from models import CanisterType
from seed_data import seed_canister_types

test_db = SqliteDatabase(':memory:')

@pytest.fixture
def setup_db():
    test_db.bind([CanisterType])
    test_db.connect()
    test_db.create_tables([CanisterType])
    yield
    test_db.drop_tables([CanisterType])
    test_db.close()

def test_seed_canister_types(setup_db):
    seed_canister_types()
    types = list(CanisterType.select())
    assert len(types) >= 2
    coleman_240 = CanisterType.get(CanisterType.name == "Coleman 240g")
    assert coleman_240.full_weight == 361
    assert coleman_240.empty_weight == 122

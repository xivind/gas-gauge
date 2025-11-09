import pytest
from peewee import SqliteDatabase
import sys
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create test database BEFORE any imports
# Use file::memory: with shared cache to allow database access from multiple threads (needed for FastAPI TestClient)
# The cache=shared parameter allows multiple connections to share the same in-memory database
test_db = SqliteDatabase('file::memory:?cache=shared', uri=True, pragmas={
    'foreign_keys': 1,
})

# Replace the production database with test database BEFORE importing models
import database
database.db = test_db

# Mock init_db to prevent it from being called during import
original_init_db = database.init_db
database.init_db = lambda: None

# Now we can safely import models and they will use the test database
from models import CanisterType, Canister, Weighing

# Immediately bind and setup the test database
test_db.bind([CanisterType, Canister, Weighing], bind_refs=False, bind_backrefs=False)
test_db.connect()
test_db.create_tables([CanisterType, Canister, Weighing])

@pytest.fixture(autouse=True)
def setup_db():
    """Clean database between tests"""
    yield
    # Clear all data between tests
    test_db.execute_sql('DELETE FROM weighing')
    test_db.execute_sql('DELETE FROM canister')
    test_db.execute_sql('DELETE FROM canistertype')

@pytest.fixture
def client():
    """Create FastAPI test client"""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)

@pytest.fixture
def canister():
    """Create test canister with type"""
    ct = CanisterType.create(name="Coleman 240g", full_weight=361, empty_weight=122)
    return Canister.create(label="Test Canister", canister_type=ct, status="active")

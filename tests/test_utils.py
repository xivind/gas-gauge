import pytest
import re
from utils import generate_canister_id


def test_generate_canister_id_format():
    """Test that generated ID matches expected format"""
    canister_id = generate_canister_id()

    # Should match GC-{6 hex chars}{4 digits}
    pattern = r'^GC-[a-f0-9]{6}\d{4}$'
    assert re.match(pattern, canister_id), f"ID {canister_id} doesn't match pattern"

    # Should be exactly 13 characters
    assert len(canister_id) == 13


def test_generate_canister_id_uniqueness():
    """Test that consecutive IDs are different"""
    id1 = generate_canister_id()
    id2 = generate_canister_id()

    assert id1 != id2

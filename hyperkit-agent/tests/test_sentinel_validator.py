"""
Tests for Sentinel Object Validator Utility
"""

import pytest
from cli.utils.sentinel_validator import (
    is_sentinel,
    validate_and_convert,
    validate_string_param,
    validate_path_param
)


class MockSentinel:
    """Mock Click Sentinel object for testing"""
    pass


@pytest.mark.unit
def test_is_sentinel_with_sentinel():
    """Test is_sentinel detects Sentinel objects"""
    sentinel = MockSentinel()
    # Mock the type string to include 'Sentinel'
    sentinel.__class__.__name__ = 'Sentinel'
    assert is_sentinel(sentinel) is True


@pytest.mark.unit
def test_is_sentinel_with_none():
    """Test is_sentinel returns False for None"""
    assert is_sentinel(None) is False


@pytest.mark.unit
def test_is_sentinel_with_string():
    """Test is_sentinel returns False for normal strings"""
    assert is_sentinel("test") is False


@pytest.mark.unit
def test_validate_and_convert_sentinel():
    """Test validate_and_convert handles Sentinel objects"""
    sentinel = MockSentinel()
    sentinel.__class__.__name__ = 'Sentinel'
    result = validate_and_convert(sentinel, default="default")
    assert result == "default"


@pytest.mark.unit
def test_validate_and_convert_valid():
    """Test validate_and_convert returns valid values"""
    assert validate_and_convert("test", default="default") == "test"
    assert validate_and_convert(123, default="default") == 123


@pytest.mark.unit
def test_validate_string_param_sentinel():
    """Test validate_string_param handles Sentinel objects"""
    sentinel = MockSentinel()
    sentinel.__class__.__name__ = 'Sentinel'
    result = validate_string_param(sentinel)
    assert result is None


@pytest.mark.unit
def test_validate_string_param_valid():
    """Test validate_string_param returns valid strings"""
    assert validate_string_param("test") == "test"
    assert validate_string_param("  test  ") == "test"
    assert validate_string_param(123) == "123"


@pytest.mark.unit
def test_validate_string_param_empty():
    """Test validate_string_param handles empty strings"""
    assert validate_string_param("") is None
    assert validate_string_param("   ") is None


@pytest.mark.unit
def test_validate_path_param_safe():
    """Test validate_path_param validates safe paths"""
    assert validate_path_param("workflow_123") == "workflow_123"
    assert validate_path_param("test/workflow") == "test/workflow"


@pytest.mark.unit
def test_validate_path_param_unsafe():
    """Test validate_path_param rejects unsafe paths"""
    assert validate_path_param("../workflow") is None
    assert validate_path_param("/absolute/path") is None
    assert validate_path_param("") is None


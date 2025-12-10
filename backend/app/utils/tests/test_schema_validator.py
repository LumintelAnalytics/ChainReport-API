import pytest
import json
import os
from jsonschema import ValidationError
import backend.app.utils.schema_validator as schema_validator

# Define a temporary schema path for testing
TEST_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'temp_test_report_schema.json')

@pytest.fixture(scope="module")
def setup_teardown_schema(monkeypatch):
    """Sets up a temporary schema file for testing and tears it down afterwards."""
    # Create a dummy schema for testing
    test_schema = {
        "type": "object",
        "properties": {
            "report_id": {"type": "string"},
            "status": {"type": "string"},
            "data": {"type": "object"}
        },
        "required": ["report_id", "status", "data"]
    }
    with open(TEST_SCHEMA_PATH, 'w') as f:
        json.dump(test_schema, f)

    # Temporarily override the SCHEMA_PATH for the duration of the tests
    monkeypatch.setattr(schema_validator, 'SCHEMA_PATH', TEST_SCHEMA_PATH)
    monkeypatch.setattr(schema_validator, 'REPORT_SCHEMA', schema_validator.load_schema())

    yield

    # Teardown: Remove the dummy schema file
    os.remove(TEST_SCHEMA_PATH)

def test_load_schema_success(_setup_teardown_schema):
    """Test that the schema can be loaded successfully."""
    schema = schema_validator.load_schema()
    assert isinstance(schema, dict)
    assert "report_id" in schema["properties"]

def test_load_schema_file_not_found(monkeypatch):
    """Test that FileNotFoundError is raised when schema file is not found."""
    monkeypatch.setattr(schema_validator, 'SCHEMA_PATH', "non_existent_file.json")
    monkeypatch.setattr(schema_validator, 'REPORT_SCHEMA', None) # Clear cached schema to force reload
    with pytest.raises(FileNotFoundError):
        schema_validator.load_schema()

def test_validate_report_success(_setup_teardown_schema):
    """Test successful validation of a well-formed report."""
    valid_report = {
        "report_id": "123",
        "status": "completed",
        "data": {"key": "value"}
    }
    try:
        schema_validator.validate_report(valid_report)
        assert True # No exception means success
    except ValidationError:
        pytest.fail("Validation failed for a valid report.")

def test_validate_report_failure_missing_field(_setup_teardown_schema):
    """Test that validation fails for a report missing a required field."""
    invalid_report = {
        "report_id": "123",
        "data": {"key": "value"}
    } # Missing 'status'
    with pytest.raises(ValidationError):
        schema_validator.validate_report(invalid_report)

def test_validate_report_failure_invalid_type(_setup_teardown_schema):
    """Test that validation fails for a report with an invalid field type."""
    invalid_report = {
        "report_id": 123, # Should be string
        "status": "completed",
        "data": {"key": "value"}
    }
    with pytest.raises(ValidationError):
        schema_validator.validate_report(invalid_report)

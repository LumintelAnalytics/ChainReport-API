import pytest
import json
import os
from jsonschema import ValidationError
from backend.app.utils.schema_validator import validate_report, load_schema, SCHEMA_PATH

# Define a temporary schema path for testing
TEST_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'temp_test_report_schema.json')

@pytest.fixture(scope="module")
def setup_teardown_schema():
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
    original_schema_path = SCHEMA_PATH
    # Note: This direct modification of a module-level variable is generally discouraged
    # but is done here for testing purposes to redirect the schema loading.
    # A more robust solution for a real application might involve dependency injection.
    global SCHEMA_PATH # pylint: disable=W0603
    SCHEMA_PATH = TEST_SCHEMA_PATH

    yield

    # Teardown: Remove the dummy schema file
    os.remove(TEST_SCHEMA_PATH)
    # Restore original SCHEMA_PATH
    SCHEMA_PATH = original_schema_path # pylint: disable=W0603

def test_load_schema_success(setup_teardown_schema):
    """Test that the schema can be loaded successfully."""
    schema = load_schema()
    assert isinstance(schema, dict)
    assert "report_id" in schema["properties"]

def test_load_schema_file_not_found():
    """Test that FileNotFoundError is raised when schema file is not found."""
    original_schema_path = SCHEMA_PATH
    global SCHEMA_PATH # pylint: disable=W0603
    SCHEMA_PATH = "non_existent_file.json"
    with pytest.raises(FileNotFoundError):
        load_schema()
    SCHEMA_PATH = original_schema_path # pylint: disable=W0603

def test_validate_report_success(setup_teardown_schema):
    """Test successful validation of a well-formed report."""
    valid_report = {
        "report_id": "123",
        "status": "completed",
        "data": {"key": "value"}
    }
    try:
        validate_report(valid_report)
        assert True # No exception means success
    except ValidationError:
        pytest.fail("Validation failed for a valid report.")

def test_validate_report_failure_missing_field(setup_teardown_schema):
    """Test that validation fails for a report missing a required field."""
    invalid_report = {
        "report_id": "123",
        "data": {"key": "value"}
    } # Missing 'status'
    with pytest.raises(ValidationError):
        validate_report(invalid_report)

def test_validate_report_failure_invalid_type(setup_teardown_schema):
    """Test that validation fails for a report with an invalid field type."""
    invalid_report = {
        "report_id": 123, # Should be string
        "status": "completed",
        "data": {"key": "value"}
    }
    with pytest.raises(ValidationError):
        validate_report(invalid_report)

import json
import os
from jsonschema import validate, ValidationError
from backend.app.core.logger import get_logger

logger = get_logger(__name__)

# Determine the path to the schema file
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'schema', 'report_schema.json')

def load_schema():
    """Loads the JSON schema from the report_schema.json file."""
    try:
        with open(SCHEMA_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Schema file not found at {SCHEMA_PATH}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from schema file at {SCHEMA_PATH}")
        raise

REPORT_SCHEMA = load_schema()

def validate_report(report_data: dict):
    """
    Validates a generated report against the loaded JSON schema.

    Args:
        report_data: The report data (dictionary) to validate.

    Raises:
        ValidationError: If the report data does not conform to the schema.
    """
    try:
        validate(instance=report_data, schema=REPORT_SCHEMA)
        logger.info("Report validated successfully against schema.")
    except ValidationError as e:
        logger.error(f"Report validation failed: {e.message}")
        logger.error(f"Validation path: {list(e.path)}")
        logger.error(f"Validator: {e.validator} with value {e.validator_value}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during report validation: {e}")
        raise

def _check_optional_fields(data: dict, schema: dict, path: list = None):
    if path is None:
        path = []

    if not isinstance(data, dict):
        return

    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))

    for key, prop_schema in properties.items():
        current_path = path + [key]
        if key not in data and key not in required_fields:
            logger.warning(f"Optional field missing: {'.'.join(current_path)}")
        elif key in data and isinstance(data[key], dict) and isinstance(prop_schema, dict):
            _check_optional_fields(data[key], prop_schema, current_path)
        elif key in data and isinstance(data[key], list) and isinstance(prop_schema, dict) and "items" in prop_schema:
            item_schema = prop_schema["items"]
            for i, item in enumerate(data[key]):
                if isinstance(item, dict) and isinstance(item_schema, dict):
                    _check_optional_fields(item, item_schema, current_path + [str(i)])

def validate_report(report_data: dict):
    """
    Validates a generated report against the loaded JSON schema.
    Returns warnings for missing optional fields.

    Args:
        report_data: The report data (dictionary) to validate.

    Raises:
        ValidationError: If the report data does not conform to the schema (for required fields).
    """
    try:
        validate(instance=report_data, schema=REPORT_SCHEMA)
        logger.info("Report validated successfully against schema.")
        _check_optional_fields(report_data, REPORT_SCHEMA)
    except ValidationError as e:
        logger.error(f"Report validation failed: {e.message}")
        logger.error(f"Validation path: {list(e.path)}")
        logger.error(f"Validator: {e.validator} with value {e.validator_value}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during report validation: {e}")
        raise

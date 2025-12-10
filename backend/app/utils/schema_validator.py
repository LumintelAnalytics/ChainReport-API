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

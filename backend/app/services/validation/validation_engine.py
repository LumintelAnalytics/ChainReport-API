"""
Validation engine for ensuring data quality and consistency before NLG and summary generation.
"""

from typing import Dict, Any, Optional, List
from copy import deepcopy

DEFAULT_ESSENTIAL_FIELDS = ["report_id", "project_name", "summary"] # Example default essential fields

def validate_field_consistency(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the consistency of fields within the provided data.
    This function should implement checks to ensure that related fields
    have consistent values.

    Args:
        data: The input data dictionary to validate.

    Returns:
        A dictionary containing validation results, including any inconsistencies found.

    Raises:
        NotImplementedError: This function is not yet implemented.
    """
    raise NotImplementedError('validate_field_consistency is not yet implemented')

def check_missing_values(data: Dict[str, Any], essential_fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Checks for missing essential values in the provided data.
    This function identifies any critical fields that are empty or None.

    Args:
        data: The input data dictionary to check.
        essential_fields: Optional list of essential fields to check. If None, uses DEFAULT_ESSENTIAL_FIELDS.

    Returns:
        A dictionary containing validation results, including any missing values found.

    Raises:
        TypeError: If data is not a dictionary.
        ValueError: If data is None.
    """
    if data is None:
        raise ValueError('data must not be None')
    if not isinstance(data, dict):
        raise TypeError('data must be a dict')

    missing_values = []
    fields_to_check = essential_fields if essential_fields is not None else DEFAULT_ESSENTIAL_FIELDS
    for field in fields_to_check:
        if field not in data or data[field] is None or data[field] == "":
            missing_values.append(field)

    if missing_values:
        return {"missing_values": f"FAILED: Missing fields: {', '.join(missing_values)}"}
    else:
        return {"missing_values": "PASSED"}

def perform_cross_source_checks(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs cross-source validation checks to ensure consistency across different data sources.
    Compares tokenomics.circulating_supply from onchain sources with supply values extracted
    from documentation or whitepapers. If mismatched, creates warning entries stored under
    `alerts` in the validation results.

    Args:
        data: The aggregated data dictionary from various sources.

    Returns:
        A dictionary containing validation results for cross-source checks, including alerts.
    """
    validation_results: Dict[str, Any] = {"alerts": []}

    has_invalid_onchain = False
    has_invalid_doc = False

    onchain_supply_str = data.get("tokenomics", {}).get("data", {}).get("circulating_supply")
    doc_supply_str = data.get("team_documentation", {}).get("whitepaper_summary", {}).get("circulating_supply")

    onchain_supply: Optional[float] = None
    doc_supply: Optional[float] = None

    try:
        if onchain_supply_str:
            onchain_supply = float(onchain_supply_str.replace(",", ""))
    except ValueError:
        validation_results["alerts"].append(
            "WARNING: Onchain circulating supply is not a valid number."
        )
        has_invalid_onchain = True

    try:
        if doc_supply_str:
            doc_supply = float(doc_supply_str.replace(",", ""))
    except ValueError:
        validation_results["alerts"].append(
            "WARNING: Documentation circulating supply is not a valid number."
        )
        has_invalid_doc = True

    if onchain_supply is not None and doc_supply is not None:
        if onchain_supply != doc_supply:
            validation_results["alerts"].append(
                f"WARNING: Circulating supply mismatch: Onchain ({onchain_supply}) vs. Documentation ({doc_supply})."
            )
        else:
            validation_results["circulating_supply_consistency"] = "PASSED"
    elif onchain_supply is None and doc_supply is None:
        # Only add this info if no specific invalid number warnings were already added for both
        if not (has_invalid_onchain and has_invalid_doc):
            validation_results["alerts"].append(
                "INFO: Circulating supply not found in both onchain and documentation sources."
            )
    elif onchain_supply is None:
        validation_results["alerts"].append(
            "INFO: Onchain circulating supply not found."
        )
    elif doc_supply is None:
        validation_results["alerts"].append(
            "INFO: Documentation circulating supply not found."
        )

    if validation_results["alerts"]:
        validation_results["cross_source_checks"] = "COMPLETED_WITH_ALERTS"
    else:
        validation_results["cross_source_checks"] = "PASSED"

    return validation_results


def normalize_missing(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes the input data by replacing missing or empty fields with explicit placeholders
    and generates a `missing_data_report` explaining the gaps.

    Args:
        data: The input data dictionary to normalize.

    Returns:
        A new dictionary with missing fields normalized and a `missing_data_report`.
    """
    normalized_data = deepcopy(data)
    missing_data_report = {}

    def _traverse_and_normalize(current_data, path):
        if isinstance(current_data, dict):
            for key, value in current_data.items():
                new_path = f"{path}.{key}" if path else key
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    normalized_data_ref = normalized_data
                    path_parts = new_path.split('.')
                    # Navigate to the correct nested dictionary in normalized_data
                    for part in path_parts[:-1]:
                        normalized_data_ref = normalized_data_ref.setdefault(part, {})
                    normalized_data_ref[path_parts[-1]] = "N/A"  # Replace with placeholder
                    missing_data_report[new_path] = "Missing or empty field replaced with 'N/A'."
                elif isinstance(value, (dict, list)):
                    _traverse_and_normalize(value, new_path)
        elif isinstance(current_data, list):
            for index, item in enumerate(current_data):
                new_path = f"{path}[{index}]"
                if item is None or (isinstance(item, str) and item.strip() == ""):
                    normalized_data_ref = normalized_data
                    path_parts = new_path.replace(']', '').split('[')
                    # Navigate to the correct nested structure in normalized_data
                    for i, part in enumerate(path_parts[:-1]):
                        if part.isdigit():
                            normalized_data_ref = normalized_data_ref[int(part)]
                        else:
                            normalized_data_ref = normalized_data_ref.setdefault(part, {})
                    if path_parts[-1].isdigit():
                        normalized_data_ref[int(path_parts[-1])] = "N/A"
                    else:
                        normalized_data_ref[path_parts[-1]] = "N/A"
                    missing_data_report[new_path] = "Missing or empty field replaced with 'N/A'."
                elif isinstance(item, (dict, list)):
                    _traverse_and_normalize(item, new_path)

    _traverse_and_normalize(data, "")
    normalized_data["missing_data_report"] = missing_data_report
    return normalized_data

# You can add more validation functions as needed.

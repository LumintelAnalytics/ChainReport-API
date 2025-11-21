import pytest
from backend.app.services.validation.validation_engine import perform_cross_source_checks, normalize_missing

def test_normalize_missing():
    data = {
        "field1": "value1",
        "field2": None,
        "field3": "",
        "nested": {
            "nested_field1": "nested_value1",
            "nested_field2": None,
            "nested_field3": ""
        },
        "list_field": [
            "item1",
            None,
            "item3",
            ""
        ]
    }

    expected_normalized_data = {
        "field1": "value1",
        "field2": "N/A",
        "field3": "N/A",
        "nested": {
            "nested_field1": "nested_value1",
            "nested_field2": "N/A",
            "nested_field3": "N/A"
        },
        "list_field": [
            "item1",
            "N/A",
            "item3",
            "N/A"
        ],
        "missing_data_report": {
            "field2": "Missing or empty field replaced with 'N/A'.",
            "field3": "Missing or empty field replaced with 'N/A'.",
            "nested.nested_field2": "Missing or empty field replaced with 'N/A'.",
            "nested.nested_field3": "Missing or empty field replaced with 'N/A'.",
            "list_field[1]": "Missing or empty field replaced with 'N/A'.",
            "list_field[3]": "Missing or empty field replaced with 'N/A'."
        }
    }

    import copy
    original_data = copy.deepcopy(data)
    normalized_data = normalize_missing(data)
    assert normalized_data == expected_normalized_data
    assert data == original_data

def test_circulating_supply_match():
    data = {
        "tokenomics": {"data": {"circulating_supply": "1000000"}},
        "team_documentation": {"whitepaper_summary": {"circulating_supply": "1,000,000"}}
    }
    result = perform_cross_source_checks(data)
    assert result["cross_source_checks"] == "PASSED"
    assert result["circulating_supply_consistency"] == "PASSED"
    assert not result["alerts"]

def test_circulating_supply_mismatch():
    data = {
        "tokenomics": {"data": {"circulating_supply": "1000000"}},
        "team_documentation": {"whitepaper_summary": {"circulating_supply": "1,500,000"}}
    }
    result = perform_cross_source_checks(data)
    assert result["cross_source_checks"] == "COMPLETED_WITH_ALERTS"
    assert len(result["alerts"]) == 1
    assert "Circulating supply mismatch" in result["alerts"][0]

def test_missing_onchain_supply():
    data = {
        "tokenomics": {"data": {}},
        "team_documentation": {"whitepaper_summary": {"circulating_supply": "1,000,000"}}
    }
    result = perform_cross_source_checks(data)
    assert result["cross_source_checks"] == "COMPLETED_WITH_ALERTS"
    assert len(result["alerts"]) == 1
    assert "Onchain circulating supply not found" in result["alerts"][0]

def test_missing_doc_supply():
    data = {
        "tokenomics": {"data": {"circulating_supply": "1000000"}},
        "team_documentation": {"whitepaper_summary": {}}
    }
    result = perform_cross_source_checks(data)
    assert result["cross_source_checks"] == "COMPLETED_WITH_ALERTS"
    assert len(result["alerts"]) == 1
    assert "Documentation circulating supply not found" in result["alerts"][0]

def test_both_supplies_missing():
    data = {
        "tokenomics": {"data": {}},
        "team_documentation": {"whitepaper_summary": {}}
    }
    result = perform_cross_source_checks(data)
    assert result["cross_source_checks"] == "COMPLETED_WITH_ALERTS"
    assert len(result["alerts"]) == 1
    assert "Circulating supply not found in both" in result["alerts"][0]

def test_invalid_onchain_supply():
    data = {
        "tokenomics": {"data": {"circulating_supply": "abc"}},
        "team_documentation": {"whitepaper_summary": {"circulating_supply": "1,000,000"}}
    }
    result = perform_cross_source_checks(data)
    assert result["cross_source_checks"] == "COMPLETED_WITH_ALERTS"
    assert len(result["alerts"]) == 2 # One WARNING for invalid onchain, one INFO for onchain not found
    assert "WARNING: Onchain circulating supply is not a valid number." in result["alerts"]
    assert "INFO: Onchain circulating supply not found." in result["alerts"]

def test_invalid_doc_supply():
    data = {
        "tokenomics": {"data": {"circulating_supply": "1000000"}},
        "team_documentation": {"whitepaper_summary": {"circulating_supply": "xyz"}}
    }
    result = perform_cross_source_checks(data)
    assert result["cross_source_checks"] == "COMPLETED_WITH_ALERTS"
    assert len(result["alerts"]) == 2 # One for invalid doc, one for info about not found
    assert "WARNING: Documentation circulating supply is not a valid number." in result["alerts"]
    assert "INFO: Documentation circulating supply not found." in result["alerts"]

def test_both_supplies_invalid():
    data = {
        "tokenomics": {"data": {"circulating_supply": "abc"}},
        "team_documentation": {"whitepaper_summary": {"circulating_supply": "xyz"}}
    }
    result = perform_cross_source_checks(data)
    assert result["cross_source_checks"] == "COMPLETED_WITH_ALERTS"
    assert len(result["alerts"]) == 2 # Only two warnings for invalid numbers, no redundant info message
    assert "WARNING: Onchain circulating supply is not a valid number." in result["alerts"]
    assert "WARNING: Documentation circulating supply is not a valid number." in result["alerts"]

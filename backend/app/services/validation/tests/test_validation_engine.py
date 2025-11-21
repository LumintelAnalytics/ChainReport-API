import pytest
from backend.app.services.validation.validation_engine import perform_cross_source_checks

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
    assert len(result["alerts"]) == 2 # One for invalid onchain, one for mismatch (since doc is valid)
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

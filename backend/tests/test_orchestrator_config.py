import pytest
from unittest.mock import patch, MagicMock
from backend.app.core.orchestrator import create_orchestrator
from backend.app.core.config import settings
import logging

@pytest.fixture(autouse=True)
def reset_settings():
    # Reset settings to default or known state before each test
    original_onchain_url = settings.ONCHAIN_METRICS_URL
    original_tokenomics_url = settings.TOKENOMICS_URL
    settings.ONCHAIN_METRICS_URL = None
    settings.TOKENOMICS_URL = None
    yield
    settings.ONCHAIN_METRICS_URL = original_onchain_url
    settings.TOKENOMICS_URL = original_tokenomics_url

@pytest.mark.asyncio
async def test_create_orchestrator_with_valid_urls():
    with patch('backend.app.core.orchestrator.orchestrator_logger') as mock_logger:
        settings.ONCHAIN_METRICS_URL = "https://valid.com/onchain"
        settings.TOKENOMICS_URL = "https://valid.com/tokenomics"
        
        orchestrator = create_orchestrator()
        
        agents = orchestrator.get_agents()
        assert 'onchain_metrics_agent' in agents
        assert 'tokenomics_agent' in agents
        mock_logger.warning.assert_not_called()

@pytest.mark.asyncio
async def test_create_orchestrator_with_missing_onchain_url():
    with patch('backend.app.core.orchestrator.orchestrator_logger') as mock_logger:
        settings.ONCHAIN_METRICS_URL = None # Missing
        settings.TOKENOMICS_URL = "https://valid.com/tokenomics"
        
        orchestrator = create_orchestrator()
        
        agents = orchestrator.get_agents()
        assert 'onchain_metrics_agent' not in agents
        assert 'tokenomics_agent' in agents
        mock_logger.warning.assert_called_with(
            "Configuration Error: ONCHAIN_METRICS_URL is missing. Skipping agent registration."
        )

@pytest.mark.asyncio
async def test_create_orchestrator_with_invalid_onchain_url():
    with patch('backend.app.core.orchestrator.orchestrator_logger') as mock_logger:
        settings.ONCHAIN_METRICS_URL = "invalid-url" # Invalid
        settings.TOKENOMICS_URL = "https://valid.com/tokenomics"
        
        orchestrator = create_orchestrator()
        
        agents = orchestrator.get_agents()
        assert 'onchain_metrics_agent' not in agents
        assert 'tokenomics_agent' in agents
        mock_logger.warning.assert_called_with(
            "Configuration Error: ONCHAIN_METRICS_URL ('invalid-url') is not a valid HTTP/HTTPS URL. Skipping agent registration."
        )

@pytest.mark.asyncio
async def test_create_orchestrator_with_missing_tokenomics_url():
    with patch('backend.app.core.orchestrator.orchestrator_logger') as mock_logger:
        settings.ONCHAIN_METRICS_URL = "https://valid.com/onchain"
        settings.TOKENOMICS_URL = None # Missing
        
        orchestrator = create_orchestrator()
        
        agents = orchestrator.get_agents()
        assert 'onchain_metrics_agent' in agents
        assert 'tokenomics_agent' not in agents
        mock_logger.warning.assert_called_with(
            "Configuration Error: TOKENOMICS_URL is missing. Skipping agent registration."
        )

@pytest.mark.asyncio
async def test_create_orchestrator_with_invalid_tokenomics_url():
    with patch('backend.app.core.orchestrator.orchestrator_logger') as mock_logger:
        settings.ONCHAIN_METRICS_URL = "https://valid.com/onchain"
        settings.TOKENOMICS_URL = "ftp://invalid.com" # Invalid scheme
        
        orchestrator = create_orchestrator()
        
        agents = orchestrator.get_agents()
        assert 'onchain_metrics_agent' in agents
        assert 'tokenomics_agent' not in agents
        mock_logger.warning.assert_called_with(
            "Configuration Error: TOKENOMICS_URL ('ftp://invalid.com') is not a valid HTTP/HTTPS URL. Skipping agent registration."
        )

@pytest.mark.asyncio
async def test_create_orchestrator_with_no_urls():
    with patch('backend.app.core.orchestrator.orchestrator_logger') as mock_logger:
        settings.ONCHAIN_METRICS_URL = None
        settings.TOKENOMICS_URL = None
        
        orchestrator = create_orchestrator()
        
        agents = orchestrator.get_agents()
        assert 'onchain_metrics_agent' not in agents
        assert 'tokenomics_agent' not in agents
        assert mock_logger.warning.call_count == 2
        mock_logger.warning.assert_any_call(
            "Configuration Error: ONCHAIN_METRICS_URL is missing. Skipping agent registration."
        )
        mock_logger.warning.assert_any_call(
            "Tokenomics agent will not be registered due to invalid configuration."
        )

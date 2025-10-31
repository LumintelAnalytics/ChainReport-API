import pytest
import threading
from unittest.mock import patch

from backend.app.services.report_processor import process_report
from backend.app.core import storage

@pytest.fixture(autouse=True)
def clear_report_store():
    storage.REPORT_STORE.clear()

def test_process_report_success():
    report_id = "test_report_1"
    token_id = "test_token_1"
    
    # Mock the agents to prevent actual external calls
    with patch('backend.app.services.agents.price_agent.PriceAgent.get_price') as mock_get_price:
        with patch('backend.app.services.agents.volume_agent.VolumeAgent.get_volume') as mock_get_volume:
            with patch('backend.app.services.agents.trend_agent.TrendAgent.get_trend') as mock_get_trend:
        
                mock_get_price.return_value = 100.0
                mock_get_volume.return_value = 1000.0
                mock_get_trend.return_value = "up"

                process_report(report_id, token_id)

                assert storage.get_report_status(report_id) == "completed"
                report_data = storage.REPORT_STORE[report_id]["data"]
                assert report_data["price"] == 100.0
                assert report_data["volume"] == 1000.0
                assert report_data["trend"] == "up"

def test_process_report_already_processing():
    report_id = "test_report_2"
    token_id = "test_token_2"
    storage.set_report_status(report_id, "processing")

    with pytest.raises(ValueError, match=f"Report {report_id} is already being processed"):
        process_report(report_id, token_id)
    
    assert storage.get_report_status(report_id) == "processing"

def test_process_report_failure_sets_failed_status():
    report_id = "test_report_3"
    token_id = "test_token_3"

    with patch('backend.app.services.agents.price_agent.PriceAgent.get_price') as mock_get_price:
        mock_get_price.side_effect = Exception("Agent error")
        with pytest.raises(Exception, match="Agent error"):
            process_report(report_id, token_id)
    
    assert storage.get_report_status(report_id) == "failed"

def test_try_set_processing_success():
    report_id = "new_report"
    assert storage.try_set_processing(report_id) is True
    assert storage.get_report_status(report_id) == "processing"

def test_try_set_processing_failure_already_processing():
    report_id = "existing_report"
    storage.set_report_status(report_id, "processing")
    assert storage.try_set_processing(report_id) is False
    assert storage.get_report_status(report_id) == "processing"

def test_try_set_processing_failure_other_status():
    report_id = "existing_report_completed"
    storage.set_report_status(report_id, "completed")
    assert storage.try_set_processing(report_id) is True
    assert storage.get_report_status(report_id) == "processing"

def test_concurrent_processing_only_one_succeeds():
    report_id = "concurrent_report"
    token_id = "concurrent_token"
    
    processed_count = 0
    exception_count = 0

    def worker():
        nonlocal processed_count, exception_count
        try:
            # Mock the agents to prevent actual external calls
            with patch('backend.app.services.agents.price_agent.PriceAgent.get_price', return_value=100.0):
                with patch('backend.app.services.agents.volume_agent.VolumeAgent.get_volume', return_value=1000.0):
                    with patch('backend.app.services.agents.trend_agent.TrendAgent.get_trend', return_value="up"):
                        process_report(report_id, token_id)
            processed_count += 1
        except ValueError as e:
            if "already being processed" in str(e):
                exception_count += 1
            else:
                raise
        except Exception:
            # Catch other unexpected exceptions during processing
            pass

    threads = []
    for _ in range(5):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    assert processed_count == 1
    assert exception_count == 4
    assert storage.get_report_status(report_id) == "completed"
    assert "data" in storage.REPORT_STORE[report_id]

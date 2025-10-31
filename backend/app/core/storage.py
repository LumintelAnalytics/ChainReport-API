
import threading

REPORT_STORE = {}
_report_store_lock = threading.Lock()

def set_report_status(report_id: str, status: str):
    """Sets the status of a report."""
    with _report_store_lock:
        if report_id not in REPORT_STORE:
            REPORT_STORE[report_id] = {"status": status, "data": None}
        else:
            REPORT_STORE[report_id]["status"] = status

def get_report_status(report_id: str) -> str | None:
    """Gets the status of a report."""
    with _report_store_lock:
        return REPORT_STORE.get(report_id, {}).get("status")

def try_set_processing(report_id: str) -> bool:
    """
    Atomically checks if a report is not processing and, if so, sets its status to "processing".
    Returns True if successful, False otherwise.
    """
    with _report_store_lock:
        if REPORT_STORE.get(report_id, {}).get("status") != "processing":
            if report_id not in REPORT_STORE:
                REPORT_STORE[report_id] = {"status": "processing", "data": None}
            else:
                REPORT_STORE[report_id]["status"] = "processing"
            return True
        return False

def save_report_data(report_id: str, data: dict):
    """Saves the data for a report."""
    with _report_store_lock:
        if report_id not in REPORT_STORE:
            REPORT_STORE[report_id] = {"status": "completed", "data": data}
        else:
            REPORT_STORE[report_id]["data"] = data
            REPORT_STORE[report_id]["status"] = "completed"

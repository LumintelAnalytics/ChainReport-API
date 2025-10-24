
REPORT_STORE = {}

def set_report_status(report_id: str, status: str):
    """Sets the status of a report."""
    if report_id not in REPORT_STORE:
        REPORT_STORE[report_id] = {"status": status, "data": None}
    else:
        REPORT_STORE[report_id]["status"] = status

def get_report_status(report_id: str) -> str | None:
    """Gets the status of a report."""
    return REPORT_STORE.get(report_id, {}).get("status")

def save_report_data(report_id: str, data: dict):
    """Saves the data for a report."""
    if report_id not in REPORT_STORE:
        REPORT_STORE[report_id] = {"status": "completed", "data": data}
    else:
        REPORT_STORE[report_id]["data"] = data
        REPORT_STORE[report_id]["status"] = "completed"

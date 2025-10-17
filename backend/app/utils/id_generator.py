import uuid

def generate_report_id() -> str:
    """
    Generates a unique alphanumeric string using uuid4().
    This ensures each report request receives a unique tracking ID.
    """
    return str(uuid.uuid4())

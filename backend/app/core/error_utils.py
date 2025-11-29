import logging
import traceback
from typing import Dict, Any

logger = logging.getLogger(__name__)

def capture_exception(e: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Captures an exception with its full stack trace and additional context,
    returning a standardized error format.

    Args:
        e: The exception object.
        context: A dictionary containing additional context, e.g.,
                 {"agent_name": "social_sentiment_agent", "report_id": "some_uuid"}.

    Returns:
        A dictionary representing the standardized error, including:
        - "error_type": The type of the exception.
        - "message": The exception message.
        - "stack_trace": The full stack trace of the exception.
        - "context": The additional context provided.
    """
    error_type = type(e).__name__
    message = str(e)
    stack_trace = traceback.format_exc()

    logger.error(
        f"Exception captured: {error_type} - {message}. Context: {context}. Stack Trace:\n{stack_trace}"
    )

    standardized_error = {
        "error_type": error_type,
        "message": message,
        "stack_trace": stack_trace,
        "context": context,
    }
    return standardized_error

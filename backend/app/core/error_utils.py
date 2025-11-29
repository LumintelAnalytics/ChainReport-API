import logging
import traceback
import os
from typing import Dict, Any

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

def capture_exception(e: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Captures an exception with its stack trace and additional context,
    returning a standardized error format.
    Stack trace verbosity is controlled by the ENVIRONMENT environment variable
    or settings.DEBUG. In production, stack traces are sanitized/truncated.

    Args:
        e: The exception object.
        context: A dictionary containing additional context, e.g.,
                 {"agent_name": "social_sentiment_agent", "report_id": "some_uuid"}.

    Returns:
        A dictionary representing the standardized error, including:
        - "error_type": The type of the exception.
        - "message": The exception message.
        - "stack_trace": The full or truncated stack trace of the exception.
        - "context": The additional context provided.
    """
    error_type = type(e).__name__
    message = str(e)
    full_stack_trace = "".join(traceback.format_exception(type(e), e, e.__traceback__)) if e.__traceback__ else "No stack trace available."
    
    stack_trace = full_stack_trace
    log_level = logger.error

    if not settings.DEBUG:  # Assuming DEBUG is False for production
        # Truncate stack trace for production environments
        lines = full_stack_trace.splitlines()
        if len(lines) > 5:  # Keep last 5 lines for brevity in production
            stack_trace = "\n".join(lines[-5:])
        
        # Log less verbosely in production
        log_level = logger.warning
        log_message = f"Exception captured: {error_type} - {message}. Context: {context}. Stack Trace (truncated):\n{stack_trace}"
    else:
        log_message = f"Exception captured: {error_type} - {message}. Context: {context}. Stack Trace:\n{stack_trace}"
    
    log_level(log_message)

    standardized_error = {
        "error_type": error_type,
        "message": message,
        "stack_trace": stack_trace,
        "context": context,
    }
    return standardized_error

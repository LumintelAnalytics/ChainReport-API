
import logging
from backend.app.core.logging_config import configure_logging

# Configure logging at the application start
configure_logging()

# Define specific loggers after configuration
api_logger = logging.getLogger("api")
services_logger = logging.getLogger("services")
orchestrator_logger = logging.getLogger("orchestrator")

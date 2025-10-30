
import logging
import os
import pathlib

# Use a path relative to the project root; allow override via LOG_DIR env var
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_LOG_DIR_ENV = os.getenv('LOG_DIR', 'logs')
LOG_DIR = pathlib.Path(_LOG_DIR_ENV)
if not LOG_DIR.is_absolute():
    LOG_DIR = PROJECT_ROOT / LOG_DIR
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / 'app.log'

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent duplicate logs from parent loggers

    # Console handler (always available)
    c_handler = logging.StreamHandler()

    # Try to create file handler, fall back to console-only if it fails
    try:
        f_handler = logging.FileHandler(str(LOG_FILE))
    except (OSError, PermissionError) as e:
        logging.warning(f"Unable to create file handler for {LOG_FILE}: {e}")
        f_handler = None

    c_handler.setLevel(logging.INFO)
    if f_handler:
        f_handler.setLevel(logging.INFO)

    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    if f_handler:
        f_handler.setFormatter(f_format)

    # Add handlers only if not already configured
    if not logger.handlers:
        logger.addHandler(c_handler)
        if f_handler:
            logger.addHandler(f_handler)

    return logger

# Define specific loggers
api_logger = get_logger("api")
services_logger = get_logger("services")
orchestrator_logger = get_logger("orchestrator")

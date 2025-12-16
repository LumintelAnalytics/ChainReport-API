import logging
from logging.handlers import RotatingFileHandler
import os
import json
from datetime import datetime

class StructuredLogger(logging.Logger):
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1):
        if extra is None:
            extra = {}
        
        # Ensure timestamp is always present and formatted correctly
        extra['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        if isinstance(msg, dict):
            # If the message is already a dict, merge it with extra
            log_entry = {**msg, **extra}
        else:
            # Otherwise, create a new dict with 'message' and extra
            log_entry = {'message': msg, **extra}
        
        # Format the log entry as JSON
        json_message = json.dumps(log_entry)
        super()._log(level, json_message, args, exc_info, None, stack_info, stacklevel)

# Set the custom logger class
logging.setLoggerClass(StructuredLogger)

def configure_logging(log_dir="logs", max_bytes=10*1024*1024, backup_count=5):
    """
    Configures logging for the application with rotating file handlers,
    timestamped logs, and structured JSON logging.
    Logs are stored in a specified directory with debug, info, and error levels.

    Args:
        log_dir (str): The directory where log files will be stored.
        max_bytes (int): The maximum size of a log file before rotation (in bytes).
        backup_count (int): The number of backup log files to keep.
    """
    os.makedirs(log_dir, exist_ok=True)

    # Base logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all

    if logger.handlers:
        return
    # Define a custom formatter for JSON output
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            try:
                # Attempt to parse the message as JSON if it's a string
                log_entry = json.loads(record.getMessage())
            except json.JSONDecodeError:
                # If not JSON, treat it as a simple message
                log_entry = {"message": record.getMessage()}

            # Add standard record attributes
            log_entry.update({
                "level": record.levelname,
                "logger": record.name,
                "pathname": record.pathname,
                "lineno": record.lineno,
                "funcName": record.funcName
            })
            
            # Add exception info if present
            if record.exc_info:
                log_entry["exc_info"] = self.formatException(record.exc_info)
            if record.stack_info:
                log_entry["stack_info"] = self.formatStack(record.stack_info)
            
            return json.dumps(log_entry)

    json_formatter = JsonFormatter()

    # --- Debug Log Handler ---
    debug_log_path = os.path.join(log_dir, "debug.log")
    debug_handler = RotatingFileHandler(debug_log_path, maxBytes=max_bytes, backupCount=backup_count)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(json_formatter)
    logger.addHandler(debug_handler)

    # --- Info Log Handler ---
    info_log_path = os.path.join(log_dir, "info.log")
    info_handler = RotatingFileHandler(info_log_path, maxBytes=max_bytes, backupCount=backup_count)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(json_formatter)
    logger.addHandler(info_handler)

    # --- Error Log Handler ---
    error_log_path = os.path.join(log_dir, "error.log")
    error_handler = RotatingFileHandler(error_log_path, maxBytes=max_bytes, backupCount=backup_count)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    logger.addHandler(error_handler)

    # Optional: Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(json_formatter) # Use JSON formatter for console as well
    logger.addHandler(console_handler)

    # --- Downloads Log Handler ---
    downloads_log_path = os.path.join(log_dir, "downloads.log")
    downloads_handler = RotatingFileHandler(downloads_log_path, maxBytes=max_bytes, backupCount=backup_count)
    downloads_handler.setLevel(logging.INFO)
    downloads_handler.setFormatter(json_formatter)
    # Create a specific logger for downloads
    downloads_logger = logging.getLogger("downloads")
    downloads_logger.addHandler(downloads_handler)
    downloads_logger.propagate = False # Prevent logs from going to the root logger


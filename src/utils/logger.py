from src.utils.config import LOGS_DIR
import os
import logging
from logging.handlers import RotatingFileHandler
import colorlog

# Define custom log levels
STATE_LEVEL = 15  # Between DEBUG and INFO
EVENT_LEVEL = 25  # Between INFO and WARNING

# Register custom log levels
logging.addLevelName(STATE_LEVEL, "STATE")
logging.addLevelName(EVENT_LEVEL, "EVENT")

# Add custom logging methods to the logger class
def state(self, message, *args, **kwargs):
    if self.isEnabledFor(STATE_LEVEL):
        self._log(STATE_LEVEL, message, args, **kwargs)

def event(self, message, *args, **kwargs):
    if self.isEnabledFor(EVENT_LEVEL):
        self._log(EVENT_LEVEL, message, args, **kwargs)

# Add the methods to the Logger class
logging.Logger.state = state
logging.Logger.event = event


def setup_logging(module_name=None, root_dir=None):
    """
    Set up logging with separate log files for each log level, organized by module.

    :param module_name: Name of the module requesting logging (creates subdirectory)
    :param root_dir: Directory to store log files
    :return: Configured logger instance
    """
    if root_dir is None:
        # Use the original LOGS_DIR if no directory specified
        root_dir = LOGS_DIR

    # Ensure the root directory exists
    os.makedirs(root_dir,exist_ok=True)

    # Create a logger instance - use module name if provided, otherwise use the general app logger
    logger_name = f"AppLogger.{module_name}" if module_name else "AppLogger"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # Capture all log levels

    # Prevent duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger

    # Define log formats
    file_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_format = colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "STATE": "blue",  # Custom color for STATE logs
            "INFO": "green",
            "EVENT": "purple",  # Custom color for EVENT logs
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    # Define log levels and corresponding log files
    levels = {
        "debug": logging.DEBUG,
        "state": STATE_LEVEL,  # Custom STATE level
        "info": logging.INFO,
        "event": EVENT_LEVEL,  # Custom EVENT level
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    # Determine the log directory based on module_name
    if module_name:
        log_dir = os.path.join(root_dir, module_name)
    else:
        log_dir = root_dir

    # Create the log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Add file handlers for each log level
    for level_name, level_value in levels.items():
        log_file = os.path.join(log_dir, f"{level_name}.log")
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(level_value)
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Console handler for real-time debugging (only add to root logger or when no module specified)
    # This prevents duplicate console output when multiple modules log messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)


    # Prevent handler propagation to avoid duplicate logs
    logger.propagate = False

    return logger


if __name__ == "__main__":
    logger = setup_logging("example_module")
    
    logger.debug("This is a debug message")
    logger.state("This is a state message")  # Custom STATE level
    logger.info("This is an info message")
    logger.event("This is an event message")  # Custom EVENT level
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
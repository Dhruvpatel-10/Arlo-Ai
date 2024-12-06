from src.common.config import AUDIO_DIR, LOGS_DIR
from pathlib import Path
import concurrent.futures
import os
import logging
from logging.handlers import RotatingFileHandler
import colorlog


def setup_logging(root_dir=LOGS_DIR):
    """
    Set up logging with separate log files for each log level.

    :param root_dir: Directory to store log files
    :return: Configured logger instance
    """
    # Ensure the log directory exists
    os.makedirs(root_dir, exist_ok=True)

    # Create a logger instance
    logger = logging.getLogger("AppLogger")
    logger.setLevel(logging.DEBUG)  # Capture all log levels

    # Prevent duplicate handlers if setup is called multiple times
    if logger.hasHandlers():
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
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    # Define log levels and corresponding log files
    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    # Add file handlers for each log level
    for level_name, level_value in levels.items():
        log_file = os.path.join(root_dir, f"{level_name}.log")
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(level_value)
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Console handler for real-time debugging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # Prevent handler propagation
    logger.propagate = False

    return logger

logger = setup_logging()

def delete_file(file):
    try:
        file.unlink()
        logger.debug(f"Deleted temporary file: {file}")
    except OSError as e:
        logger.error(f"Error deleting file {file}: {e}")

def delete_af():
    logger.info("Cleaning up generated audio and text files...")
    files_to_delete = list(Path(AUDIO_DIR).glob('*.mp3')) + list(Path(AUDIO_DIR).glob('*.txt'))
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(delete_file, files_to_delete)

if __name__ == "__main__":
    pass
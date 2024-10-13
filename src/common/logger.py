from loguru import logger
import os
from .config import  AUDIO_DIR, LOG_FILE, ERROR_LOG_FILE, SUCCESS_LOG_FILE, DEBUG_LOG_FILE
from pathlib import Path


logger.add(LOG_FILE,
    rotation="2 MB",         # Rotate after the log file reaches 2 MB
    retention="10 days",     # Keep log files for 10 days
    compression="zip",       # Compress old log files
    format="{level} | {file} | {function} |<bold>{message}</bold>", 
    level="INFO",            # Minimum level of logs to capture
    filter=lambda record: record["level"].name not in ["ERROR", "SUCCESS", "DEBUG"] 
)

logger.add(ERROR_LOG_FILE,
    rotation="1 MB",         # Rotate after the log file reaches 1 MB
    retention="5 days",      # Keep log files for 5 days
    compression="zip",       # Compress old log files
    format="{level} | {file} | {message} || | {function} ",
    level="ERROR",           # Only capture 'ERROR' and above
    filter=lambda record: record["level"].name == "ERROR" and record["level"].name != "SUCCESS" and record["level"].name != "DEBUG" # Custom filter for ERROR logs
)
logger.add(SUCCESS_LOG_FILE,
    rotation="1 MB",         # Rotate after the log file reaches 1 MB
    retention="5 days",      # Keep log files for 5 days
    compression="zip",       # Compress old log files
    format="{level} | {file} | {message}",
    level="SUCCESS",          
    filter=lambda record: record["level"].name == "SUCCESS" 
)
logger.add(DEBUG_LOG_FILE,
    rotation="1 MB",         # Rotate after the log file reaches 1 MB
    retention="5 days",      # Keep log files for 5 days
    compression="zip",       # Compress old log files
    format="{level} | {file} | {message} || {function} ",
    level="DEBUG",          
    filter=lambda record: record["level"].name == "DEBUG" 
)

def delete_af():
    logger.info("Cleaning up generated audio files...")
    for audio_file in Path(AUDIO_DIR).glob('*.mp3'):
        try:
            os.remove(audio_file)
            logger.info(f"Deleted temporary audio file: {audio_file}")
        except OSError as e:
            logger.error(f"Error deleting file {audio_file}: {e}")


    
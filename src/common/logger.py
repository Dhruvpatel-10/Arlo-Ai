from loguru import logger
import os
from .config import LOGS_DIR, AUDIO_DIR
from pathlib import Path

# Configure logging
log_file_path = os.path.join(LOGS_DIR, 'logs.log')  
error_log_file = os.path.join(LOGS_DIR, 'errors.log')
success_log_file = os.path.join(LOGS_DIR, 'success.log')
logger.remove()
# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
os.makedirs(os.path.dirname(error_log_file), exist_ok=True)
os.makedirs(os.path.dirname(success_log_file), exist_ok=True)

logger.add(log_file_path,
    rotation="2 MB",         # Rotate after the log file reaches 1 MB
    retention="10 days",     # Keep log files for 10 days
    compression="zip",       # Compress old log files
    format="{level} {file} {function} <bold>{message}</bold>", 
    level="INFO"             # Minimum level of logs to capture
)

logger.add(error_log_file,
    rotation="1 MB",         # Rotate after the log file reaches 1 MB
    retention="5 days",      # Keep log files for 5 days
    compression="zip",       # Compress old log files
    format="{level} {time} {message}",
    level="ERROR",           # Only capture 'ERROR' and above
    filter=lambda record: record["level"].name == "ERROR"  # Custom filter for ERROR logs
)
logger.add(success_log_file,
    rotation="1 MB",         # Rotate after the log file reaches 1 MB
    retention="5 days",      # Keep log files for 5 days
    compression="zip",       # Compress old log files
    format="{level} {time} {message}",
    level="SUCCESS",          
    filter=lambda record: record["level"].name == "SUCCESS" 
)

def delete_af():
    logger.info("Cleaning up generated audio files...")
    for audio_file in Path(AUDIO_DIR).glob('*.mp3'):
        try:
            os.remove(audio_file)
            logger.info(f"Deleted temporary audio file: {audio_file}")
        except OSError as e:
            logger.error(f"Error deleting file {audio_file}: {e}")


def signal_handler(sig,frame):
    logger.info(f"Signal {sig} received. Shutting down and cleaning up...")
    delete_af()
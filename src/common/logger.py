from loguru import logger
import os
from .config import CACHE_DIR, AUDIO_DIR
from pathlib import Path
import sys

# Configure logging
log_file_path = os.path.join(CACHE_DIR, 'logs.log')  
logger.remove()
# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logger.add(log_file_path,
    rotation="2 MB",         # Rotate after the log file reaches 1 MB
    retention="10 days",     # Keep log files for 10 days
    compression="zip",       # Compress old log files
    format="{time} {level} {message} ",  # Log format
    level="INFO"             # Minimum level of logs to capture
)

def delete_audio_files():
    logger.info("Cleaning up generated audio files...")
    for audio_file in Path(AUDIO_DIR).glob('*.mp3'):
        try:
            os.remove(audio_file)
            logger.info(f"Deleted temporary audio file: {audio_file}")
        except OSError as e:
            logger.error(f"Error deleting file {audio_file}: {e}")

def signal_handler(sig, frame):
    logger.info(f"Signal {sig} received. Shutting down and cleaning up...")
    delete_audio_files()

    logger.info("Audio processes have been terminated. Goodbye!")
    sys.exit(0)

if __name__ == "__main__":
    print(AUDIO_DIR)
    delete_audio_files()
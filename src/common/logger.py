from loguru import logger
import os
from .config import CACHE_DIR

# Configure logging
log_file_path = os.path.join(CACHE_DIR, 'logs.log')  

# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logger.add(log_file_path,
    rotation="2 MB",         # Rotate after the log file reaches 1 MB
    retention="10 days",     # Keep log files for 10 days
    compression="zip",       # Compress old log files
    format="{time} {level} {message} ",  # Log format
    level="INFO"             # Minimum level of logs to capture
)
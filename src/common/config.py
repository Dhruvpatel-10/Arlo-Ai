from pathlib import Path

# Define the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # Adjust this based on your actual project structure

# Define paths
DATA_DIR = PROJECT_ROOT / 'data'
IMAGES_DIR = DATA_DIR / 'images'
AUDIO_DIR = DATA_DIR / 'audio'
CACHE_DIR = DATA_DIR / 'cache'
JSON_DIR = CACHE_DIR / 'json'
LOGS_DIR = CACHE_DIR / 'logs'

# Ensure directories exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Define cache paths
URL_DIR = JSON_DIR / 'urls.json'
QUERY_DIR = JSON_DIR / 'queries.json'
HISTORY_DIR = JSON_DIR / 'history.json'
FUNC_CACHE_DIR = JSON_DIR / 'function_cache.json'
LOG_FILE = LOGS_DIR / 'logs.log'
ERROR_LOG_FILE = LOGS_DIR / 'errors.log'
SUCCESS_LOG_FILE = LOGS_DIR / 'success.log'
DEBUG_LOG_FILE = LOGS_DIR / 'debug.log'

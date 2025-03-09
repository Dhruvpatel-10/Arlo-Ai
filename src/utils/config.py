from pathlib import Path

# Define the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Define paths
DATA_DIR = PROJECT_ROOT / 'data'
IMAGES_DIR = DATA_DIR / 'images'
AUDIO_DIR = DATA_DIR / 'audio'
CACHE_DIR = DATA_DIR / 'cache'
LOGS_DIR = DATA_DIR / 'logs'
MODELS_DIR = DATA_DIR / 'models'
VAD_DIR = MODELS_DIR / 'vad'
WAKE_WORD_DIR = MODELS_DIR / 'wake_words'

# Ensure directories exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_DIR.mkdir(parents=True, exist_ok=True)

CACHE_DIR.mkdir(parents=True, exist_ok=True)

LOGS_DIR.mkdir(parents=True, exist_ok=True)

MODELS_DIR.mkdir(parents=True, exist_ok=True)


WAKE_WORD_DIR.mkdir(parents=True, exist_ok=True)

VAD_DIR.mkdir(parents=True, exist_ok=True)

# Define cache paths
URL_DIR = CACHE_DIR / 'urls.json'
QUERY_DIR = CACHE_DIR / 'queries.json'
HISTORY_DIR = CACHE_DIR / 'history.json'
FUNC_CACHE_DIR = CACHE_DIR /'function_cache.json'

# Define model paths
VAD_WIN_DIR = VAD_DIR / 'libpv_cobra.dll'
VAD_LINUX_DIR = VAD_DIR / 'libpv_cobra.so'
FASTER_WHISPER_MODELS_DIR = MODELS_DIR / 'faster_whisper'
FASTER_WHISPER_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Define LLM models
MAIN_LLM_MODEL = "llama-3.3-70b-versatile"
FUNC_LLM_MODEL = "llama-3.3-70b-specdec"
VISION_LLM_MODEL = "llama-3.2-90b-vision-preview"
URL_LLM_MODEL = "llama-3.3-70b-specdec"

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
CLASSIFIER_DIR = MODELS_DIR / 'classifier'
FASTER_WHISPER_MODELS_DIR = MODELS_DIR / 'faster_whisper'

# Define cache paths
URL_PATH = CACHE_DIR / 'urls.json'
QUERY_PATH = CACHE_DIR / 'queries.json'
HISTORY_PATH = CACHE_DIR / 'history.json'
PROMPT_CLASSIFER_PATH = CACHE_DIR /'prompt_classification_cache.json'
CHROMADB_PATH = DATA_DIR / 'db/prompt_embeddings'

# Define model paths
VAD_WIN_DIR = VAD_DIR / 'libpv_cobra.dll'
VAD_LINUX_DIR = VAD_DIR / 'libpv_cobra.so'

# Define LLM models
MAIN_LLM_MODEL = "llama-3.3-70b-versatile"
FUNC_LLM_MODEL = "llama-3.3-70b-specdec"
VISION_LLM_MODEL = "llama-3.2-90b-vision-preview"
URL_LLM_MODEL = "llama-3.3-70b-specdec"
LLM_PROMPT_CLASSIFIER_MODEL = "mistral-saba-24b"
CLASSIFIER_MODEL = CLASSIFIER_DIR / 'allmini/all-MiniLM-L6-v2'

# Ensure directories exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_DIR.mkdir(parents=True, exist_ok=True)

CACHE_DIR.mkdir(parents=True, exist_ok=True)

LOGS_DIR.mkdir(parents=True, exist_ok=True)

MODELS_DIR.mkdir(parents=True, exist_ok=True)

WAKE_WORD_DIR.mkdir(parents=True, exist_ok=True)

FASTER_WHISPER_MODELS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFIER_DIR.mkdir(parents=True, exist_ok=True)

VAD_DIR.mkdir(parents=True, exist_ok=True)

CHROMADB_PATH.mkdir(parents=True, exist_ok=True)
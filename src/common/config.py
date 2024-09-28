import os
import json

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# Define paths
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
IMAGES_DIR = os.path.join(DATA_DIR, 'images')
AUDIO_DIR = os.path.join(DATA_DIR, 'audio')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')
# Ensure directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

history_file = os.path.join(CACHE_DIR, 'history.json')

def load_history():
    """Load conversation history from a JSON file."""
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    """Save conversation history to a JSON file."""
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=4)
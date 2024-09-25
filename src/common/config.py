import os

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# Define paths
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
IMAGES_DIR = os.path.join(DATA_DIR, 'images')
AUDIO_DIR = os.path.join(DATA_DIR, 'audio')

# Ensure directories exist
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

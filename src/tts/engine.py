# engine.py
import os
import uuid
import subprocess
from playsound import playsound
from src.common.logger import logger as logging
from src.common.config import AUDIO_DIR
import time

def generate_audio(text: str, voice: str = "en-US-AvaNeural", max_retries: int = 3, backoff_factor: float = 0.7) -> str:

    # Clean and format text
    limited_hash = uuid.uuid4().hex[:5]
    text_cleaned = os.linesep.join([s.strip().replace("*", "") for s in text.splitlines() if s.strip()])

    # Create directory for audio files
    dir_path = AUDIO_DIR
    os.makedirs(dir_path, exist_ok=True)

    # Define paths for unique temporary files
    timestamp = int(time.time())
    temp_f = os.path.join(dir_path, f'temp_text_{timestamp}_{limited_hash}.txt')
    mp3_file = os.path.join(dir_path, f"genAudio_{timestamp}_{limited_hash}.mp3")

    attempt = 0
    while attempt < max_retries:
        try:
            with open(temp_f, 'w', encoding='utf-8') as f:
                f.write(text_cleaned)
            command = [
                'edge-tts',
                '--voice', voice,
                '--file', temp_f,
                '--write-media', mp3_file
            ]
            
            logging.info(f"Executing command: {' '.join(command)}")
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30  # Set a timeout for the subprocess
            )

            if result.returncode == 0 and os.path.exists(mp3_file):
                logging.info(f"Successfully generated audio for text chunk: '{text_cleaned[:30]}...'")
                return mp3_file
            else:
                raise subprocess.CalledProcessError(
                    result.returncode, command, output=result.stdout, stderr=result.stderr
                )

        except subprocess.TimeoutExpired:
            attempt += 1
            if attempt < max_retries:
                sleep_time = backoff_factor 
                logging.warning(
                    f"Attempt {attempt} timed out. Retrying in {sleep_time} seconds... ({max_retries - attempt} retries left)"
                )
                time.sleep(sleep_time)
            else:
                logging.critical(
                    f"All {max_retries} attempts timed out for text chunk: '{text_cleaned[:30]}...'. Raising exception."
                )
                raise

        except subprocess.CalledProcessError as e:
            attempt += 1
            if attempt < max_retries:
                sleep_time = backoff_factor 
                logging.warning(
                    f"Attempt {attempt} failed with return code {e.returncode}. Retrying in {sleep_time} seconds... ({max_retries - attempt} retries left)"
                )
                time.sleep(sleep_time)
            else:
                logging.critical(
                    f"All {max_retries} attempts failed for text chunk: '{text_cleaned[:30]}...'. Raising exception."
                )
                logging.error(f"Command output: {e.output}")
                logging.error(f"Command error: {e.stderr}")
                raise

        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                sleep_time = backoff_factor * (2 ** (attempt - 1))
                logging.warning(
                    f"Attempt {attempt} encountered an error: {e}. Retrying in {sleep_time} seconds... ({max_retries - attempt} retries left)"
                )
                time.sleep(sleep_time)
            else:
                logging.critical(
                    f"All {max_retries} attempts failed for text chunk: '{text_cleaned[:30]}...'. Raising exception."
                )
                raise

        finally:
            if os.path.exists(temp_f):
                try:
                    os.remove(temp_f)
                    logging.info(f"Deleted temporary text file: {temp_f}")
                except Exception as e:
                    logging.error(f"Error deleting temporary text file {temp_f}: {e}")
            if not os.path.exists(mp3_file):
                logging.warning(f"MP3 file was not created: {mp3_file}")

def play_audio(mp3_file: str) -> None:

    if os.path.exists(mp3_file):
        try:
            logging.info(f"Playing audio file: {mp3_file}")
            playsound(mp3_file)
            os.remove(mp3_file)
            logging.info(f"Deleted temporary audio file: {mp3_file}")
        except Exception as e:
            logging.error(f"Failed to play the audio '{mp3_file}': {e}")
    else:
        logging.error(f"Audio file not found: {mp3_file}")

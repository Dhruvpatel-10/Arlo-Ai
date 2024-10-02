# engine.py
import os
import asyncio
from src.common.logger import logger as logging
from src.common.config import AUDIO_DIR
import time, random
import aiofiles
from playsound import playsound

async def generate_audio(text: str, voice: str = "en-US-AvaNeural", max_retries: int = 3, backoff_factor: float = 0.7) -> str:

    # Create directory for audio files
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # Define paths for unique temporary files
    unique_id = int(time.time()) + random.getrandbits(32)
    temp_f = os.path.join(AUDIO_DIR, f'temp_text_{unique_id}.txt')
    mp3_file = os.path.join(AUDIO_DIR, f"genAudio_{unique_id}.mp3")

    attempt = 0
    while attempt < max_retries:
        try:
            # Asynchronously write text to temp file
            async with aiofiles.open(temp_f, 'w', encoding='utf-8') as f:
                await f.write(text)

            command = [
                'edge-tts',
                '--voice', voice,
                '--file', temp_f,
                '--write-media', mp3_file
            ]
            # Start the subprocess asynchronously
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise asyncio.TimeoutError(f"Command timed out after 30 seconds.")

            if process.returncode == 0 and os.path.exists(mp3_file):
                logging.info(f"Successfully generated audio")
                return mp3_file
            else:
                error_msg = stderr.decode().strip() if stderr else "Unknown error."
                raise asyncio.SubprocessError(
                    f"Command failed with return code {process.returncode}. Error: {error_msg}"
                )

        except asyncio.TimeoutError:
            attempt += 1
            if attempt < max_retries:
                sleep_time = backoff_factor
                logging.error(
                    f"Attempt {attempt} timed out. Retrying in {sleep_time} seconds... ({max_retries - attempt} retries left)"
                )
                await asyncio.sleep(sleep_time)
            else:
                logging.error(
                    f"All {max_retries} attempts timed out for text chunk: '{text[:30]}...'. Raising exception."
                )
                raise

        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                sleep_time = backoff_factor * (2 ** (attempt - 1))
                logging.error(
                    f"Attempt {attempt} encountered an error: {e}. Retrying in {sleep_time} seconds... ({max_retries - attempt} retries left)"
                )
                await asyncio.sleep(sleep_time)
            else:
                logging.error(
                    f"All {max_retries} attempts failed for text chunk: '{text[:30]}...'. Raising exception."
                )
                raise
        finally:
            # Clean up temporary files
            if os.path.exists(temp_f):
                try:
                    os.remove(temp_f)
                except Exception as e:
                    logging.error(f"Error deleting temporary text file {temp_f}: {e}")
            if not os.path.exists(mp3_file):
                logging.warning(f"MP3 file was not created: {mp3_file}")

async def play_audio(mp3_file: str) -> None:

    if os.path.exists(mp3_file):
        try:
            # Run playsound in a separate thread to avoid blocking
            await asyncio.to_thread(playsound, mp3_file)
            os.remove(mp3_file)
        except Exception as e:
            logging.error(f"Failed to play the audio '{mp3_file}': {e}")
    else:
        logging.error(f"Audio file not found: {mp3_file}")



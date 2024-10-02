# audio.py
import threading
from queue import Queue
from .engine import generate_audio, play_audio
from common.logger import logger as logging

def audio_generator_worker(text_queue: Queue, audio_queue: Queue):
    
    while True:
        text_chunk = text_queue.get() 
        if text_chunk is None:
            logging.info("Audio Generator received sentinel. Exiting.")
            # Pass sentinel to audio player
            audio_queue.put(None)
            text_queue.task_done()
            break
        try:
            mp3_file = generate_audio(text=text_chunk)
            logging.info(f"Audio generated: {mp3_file}")
            audio_queue.put(mp3_file)  
        except Exception as e:
            logging.error(f"generating audio for '{text_chunk}': {e}")
        finally:
            text_queue.task_done()

def audio_player_worker(audio_queue: Queue):
    while True:
        mp3_file = audio_queue.get()  # Use get() instead of popleft()
        if mp3_file is None:
            logging.info("Audio Player received sentinel. Exiting.")
            audio_queue.task_done()
            break
        try:
            play_audio(mp3_file)
        except Exception as e:
            logging.error(f"Error playing audio '{mp3_file}': {e}")
        finally:
            audio_queue.task_done()

def start_audio_threads(text_queue: Queue, audio_queue: Queue, pool_size: int = 4):
    logging.info(f"Starting {pool_size} audio generator threads.")
    threads = []
    
    for i in range(pool_size):
        t = threading.Thread(target=audio_generator_worker, args=(text_queue, audio_queue), name=f"AudioGenerator-{i+1}")
        t.start()
        threads.append(t)
        logging.info(f"Started thread: {t.name}")
    
    player_thread = threading.Thread(target=audio_player_worker, args=(audio_queue,), name="AudioPlayer")
    player_thread.start()
    threads.append(player_thread)
    logging.info(f"Started thread: {player_thread.name}")
    
    return threads

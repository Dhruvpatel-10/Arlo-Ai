import threading
from collections import deque
from .engine import generate_audio, play_audio_sequence
from common.config import AUDIO_DIR
audio_queue = deque()
queue_lock = threading.Lock()

def generate_audio_files(text_queue, voice='en-US-AvaNeural', audio_dir=AUDIO_DIR):
    def producer():
        while text_queue:
            text_chunk = text_queue.popleft()  
            mp3_file = generate_audio(text_chunk, voice, audio_dir)
            with queue_lock:
                audio_queue.append(mp3_file)
        with queue_lock:
            audio_queue.append(None)

    def consumer():
        while True:
            with queue_lock:
                if audio_queue:
                    mp3_file = audio_queue.popleft()
                else:
                    continue
            if mp3_file is None:
                break
            play_audio_sequence([mp3_file])

    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)

    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()
    consumer_thread.join()
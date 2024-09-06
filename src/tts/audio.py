import queue
import threading
from .engine import generate_audio, play_audio_sequence
from common.config import AUDIO_DIR

audio_queue = queue.Queue()


def generate_audio_files(text_queue, voice='en-US-AvaNeural', audio_dir=AUDIO_DIR):
    def producer():
        while not text_queue.empty():
            text_chunk = text_queue.get()
            mp3_file = generate_audio(text_chunk, voice, audio_dir)
            audio_queue.put(mp3_file)
        audio_queue.put(None)  # Signal end of audio files

    def consumer():
        while True:
            mp3_file = audio_queue.get()
            if mp3_file is None:
                break  # Exit the loop when producer signals completion
            play_audio_sequence([mp3_file])

    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)

    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()
    consumer_thread.join()

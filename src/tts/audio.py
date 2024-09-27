import multiprocessing
from multiprocessing import Queue
from collections import deque
from .engine import generate_audio, play_audio_sequence
from common.config import AUDIO_DIR
import subprocess  # Ensure subprocess is imported for exception handling

def generate_audio_process(text_queue: Queue, audio_queue: Queue):
    while True:
        text_chunk = text_queue.get()
        if text_chunk is None:  # Sentinel value to indicate completion
            break
        try:
            mp3_file = generate_audio(text=text_chunk)
            audio_queue.put(mp3_file)
        except subprocess.CalledProcessError as e:
            print(f"Error in generating audio for text '{text_chunk}': {e}")

    audio_queue.put(None)  

def play_audio_process(audio_queue: Queue):
    while True:
        mp3_file = audio_queue.get()
        if mp3_file is None:  
            break
        play_audio_sequence([mp3_file])

def generate_audio_files_multiprocessing(text_queue_input):
    # Create multiprocessing queues
    text_queue = multiprocessing.Queue()
    audio_queue = multiprocessing.Queue()

    # Populate the text_queue
    for item in text_queue_input:
        text_queue.put(item)
    text_queue.put(None)  # Sentinel value to indicate no more data

    # Create the producer and consumer processes
    producer_process = multiprocessing.Process(target=generate_audio_process, args=(text_queue, audio_queue))
    consumer_process = multiprocessing.Process(target=play_audio_process, args=(audio_queue,))

    # Start both processes
    producer_process.start()
    consumer_process.start()

    # Wait for both processes to finish
    producer_process.join()
    consumer_process.join()

if __name__ == "__main__":
    # Sample text data
    text_queue = deque([
        "Hello, this is the first text.",
        "This is the second piece of text.",
        "And here is the third one."
        # Add more text chunks as needed
    ])

    # Call the multiprocessing version
    generate_audio_files_multiprocessing(text_queue, voice='en-US-AvaNeural', audio_dir=AUDIO_DIR)

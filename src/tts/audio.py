from multiprocessing import Queue, Process, Pool
from .engine import generate_audio, play_audio
from common.logger import logger as logging


def audio_generator_worker(text_chunk):
    try:
        logging.info(f"Generating audio for chunk: {text_chunk[:30]}...")
        mp3_file = generate_audio(text=text_chunk)
        logging.info(f"Audio generated for chunk: {text_chunk[:30]}...")
        return mp3_file
    except Exception as e:
        logging.error(f"Error generating audio for '{text_chunk}': {e}")
        return None

def audio_generator(text_queue: Queue, audio_queue: Queue, pool_size=4):
    pool = Pool(processes=pool_size)
    while True:
        text_chunk = text_queue.get()
        if text_chunk is None:
            logging.info("Audio Generator received sentinel. Exiting.")
            pool.close()
            pool.join()
            audio_queue.put(None)  # Pass sentinel to audio player
            break
        # Submit the text chunk to the pool
        result = pool.apply_async(audio_generator_worker, args=(text_chunk,))
        mp3_file = result.get()
        if mp3_file:
            audio_queue.put(mp3_file)

def audio_player(audio_queue: Queue):

    while True:
        mp3_file = audio_queue.get()
        if mp3_file is None:
            # Sentinel value received, terminate the player
            logging.info("Audio Player received sentinel. Exiting.")
            break
        try:
            logging.info(f"Playing audio: {mp3_file}")
            play_audio(mp3_file)
            logging.info(f"Finished playing: {mp3_file}")
        except Exception as e:
            logging.error(f"Error playing audio '{mp3_file}': {e}")
            # Optionally, handle playback errors here

def start_audio_processes(text_queue: Queue, audio_queue: Queue):
   
    generator_process = Process(target=audio_generator, args=(text_queue, audio_queue), name="AudioGenerator")
    player_process = Process(target=audio_player, args=(audio_queue,), name="AudioPlayer")

    generator_process.start()
    player_process.start()

    logging.info("Audio Generator and Audio Player processes started.")

    return generator_process, player_process
import asyncio
from asyncio import Queue
from .engine import generate_audio, play_audio
from src.common.logger import logger as logging

async def audio_generator_worker(text_queue: Queue, audio_queue: Queue):
    while True:
        index, text_chunk = await text_queue.get()
        
        if text_chunk is None:  # Using None as a sentinel value
            logging.info("Audio Generator received sentinel. Exiting.")
            await audio_queue.put((None, None))
            break
        
        try:
            mp3_file = await generate_audio(text=text_chunk)  # Assume this is an async function
            logging.success(f"Audio generated for index {index}: {text_chunk}")
            await audio_queue.put((index, mp3_file))
        except Exception as e:
            logging.error(f"Generating audio for index {index} ('{text_chunk}'): {e}")
            await audio_queue.put((index, None))  # Pass an error indicator with the same index

async def audio_player_worker(audio_queue: Queue):
    next_expected_index = 0
    buffer = {}

    while True:
        index, mp3_file = await audio_queue.get()
        
        if (index, mp3_file) == (None, None):
            logging.info("Audio Player received sentinel.")
            break
        
        if index == next_expected_index:
            if mp3_file:
                try:
                    await play_audio(mp3_file)  # Assume this is an async function
                except Exception as e:
                    logging.error(f"Error playing audio '{mp3_file}': {e}")
            else:
                logging.error(f"Audio file for index {index} is missing.")
            next_expected_index += 1
            
            # Check buffer for the next expected audio
            while next_expected_index in buffer:
                buffered_mp3 = buffer.pop(next_expected_index)
                if buffered_mp3:
                    try:
                        await play_audio(buffered_mp3)
                    except Exception as e:
                        logging.error(f"Error playing buffered audio '{buffered_mp3}': {e}")
                else:
                    logging.error(f"Buffered audio file for index {next_expected_index} is missing.")
                next_expected_index += 1
        elif index > next_expected_index:
            # Store out-of-order audio in buffer
            buffer[index] = mp3_file
            logging.info(f"Buffered audio for index {index}. Waiting for index {next_expected_index}.")
        else:
            logging.warning(f"Received duplicate or out-of-order audio for index {index}. Ignoring.")

    logging.info("Audio Player exiting.")

async def start_audio_workers(text_queue: Queue, audio_queue: Queue, pool_size: int = 4):
    logging.info(f"Starting {pool_size} audio generator workers.")
    workers = [asyncio.create_task(audio_generator_worker(text_queue, audio_queue)) for _ in range(pool_size)]
    player = asyncio.create_task(audio_player_worker(audio_queue))
    return workers + [player]

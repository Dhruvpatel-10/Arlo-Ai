import io
import asyncio
from asyncio import Queue, Semaphore, create_task, gather, to_thread
from typing import List, Tuple, Dict
import sounddevice as sd
import soundfile as sf
from tts.engines import edge, speechify
from blingfire import text_to_sentences
from tts.voices import VOICES
from common.logger import setup_logging
import numpy as np

logger = setup_logging()

class TTSManager:
    def __init__(self, max_concurrent_tasks: int = 20, audio_queue_maxsize: int = 100) -> None:
        self.engines = {
            "EdgeTTS": edge.EdgeTTS(),
            "SpeechifyTTS": speechify.SpeechifyTTS()
        }
        self.audio_queue = Queue(maxsize=audio_queue_maxsize)
        self.semaphore = Semaphore(max_concurrent_tasks)
        self.next_index_to_play = 0
        self.playback_lock = asyncio.Lock()  # Ensure one playback at a time
        self.buffer: Dict[int, Tuple[np.ndarray, int]] = {}  # Buffer to store preloaded audio (data, samplerate)
        self.playback_event = asyncio.Event()  # Event to signal playback task

    async def play_audio_async(self, audio_data: np.ndarray, samplerate: int) -> None:
        try:
            # Play audio in a separate thread to avoid blocking the event loop
            await to_thread(sd.play, audio_data, samplerate)
            # Wait for playback to finish in a separate thread
            await to_thread(sd.wait)
        except Exception as e:
            logger.error(f"Failed to play audio data: {e}", exc_info=True)

    def split_sentences(self, response: str) -> List[Tuple[int, str]]:
        sentences = text_to_sentences(response)
        split_sentences = [s.strip() for s in sentences.split('\n') if s.strip()]
        return list(enumerate(split_sentences))

    async def generate_audio(self, index: int, sentence: str, voice: str, engine: object) -> None:
        async with self.semaphore:
            try:
                audio_bytes = await engine.generate_audio_with_retry(sentence, voice)
                if audio_bytes:
                    # Pre-decode audio data here
                    with io.BytesIO(audio_bytes) as audio_file:
                        data, samplerate = await to_thread(sf.read, audio_file, dtype='float32')
                    await self.audio_queue.put((index, (data, samplerate)))
                    logger.info(f"Enqueued audio for sentence {index}")
                else:
                    logger.warning(f"No audio data returned for sentence {index}")
            except Exception as e:
                logger.error(f"Exception generating audio for sentence {index}: {e}", exc_info=True)

    async def producer(self, response: str, voice_name: str) -> None:
        VOICE = VOICES.get(voice_name, VOICES["Ava_Edge"])
        logger.info(f"Using voice '{VOICE.name}' and engine '{VOICE.engine}'")
        engine_instance = self.engines.get(VOICE.engine, self.engines["EdgeTTS"])

        tasks = [
            create_task(self.generate_audio(index, sentence, VOICE.name, engine_instance))
            for index, sentence in self.split_sentences(response)
        ]
        await gather(*tasks)
        await self.audio_queue.put(None)  # Sentinel to indicate completion

    async def consumer(self) -> None:
        while True:
            item = await self.audio_queue.get()
            if item is None:
                logger.info("Consumer received sentinel None. Exiting.")
                self.playback_event.set()  # Signal playback to check remaining buffer
                break

            index, (audio_data, samplerate) = item
            self.buffer[index] = (audio_data, samplerate)
            logger.debug(f"Consumer received audio for sentence {index}")

            self.audio_queue.task_done()
            self.playback_event.set()  # Signal playback task to attempt playing

        # After receiving sentinel, ensure all remaining audio is played
        self.playback_event.set()

    async def playback_task(self):
        while True:
            await self.playback_event.wait()
            async with self.playback_lock:
                while self.next_index_to_play in self.buffer:
                    audio_data, samplerate = self.buffer.pop(self.next_index_to_play)
                    logger.info(f"Playing audio for sentence {self.next_index_to_play}")
                    await self.play_audio_async(audio_data, samplerate)
                    logger.info(f"Played audio for sentence {self.next_index_to_play}")
                    self.next_index_to_play += 1
            self.playback_event.clear()

            # Exit condition: no more items and buffer is empty
            if self.audio_queue.empty() and not self.buffer:
                break

    async def generate_and_play_audio(self, response: str, voice_name: str = "Carly_Speechify") -> None:
        self.next_index_to_play = 0
        consumer_task = create_task(self.consumer())
        producer_task = create_task(self.producer(response, voice_name))
        playback_task = create_task(self.playback_task())

        try:
            await gather(producer_task, consumer_task, playback_task)
        except Exception as e:
            logger.error(f"Error occurred during generate and play: {e}", exc_info=True)
            producer_task.cancel()
            consumer_task.cancel()
            playback_task.cancel()
        
    
    async def close_all_engines(self):
        speechify_engine = self.engines.get("SpeechifyTTS")
        try:
            if speechify_engine and hasattr(speechify_engine, 'close'):
                await speechify_engine.close()
                logger.info("Closed SpeechifyTTS engine.")
        except Exception as e:
            logger.error(f"Error closing TTS engines: {e}", exc_info=True)
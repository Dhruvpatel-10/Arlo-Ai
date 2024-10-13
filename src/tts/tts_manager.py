import os
import asyncio
from asyncio import Queue, Semaphore, create_task, gather
from typing import Generator , Tuple
from playsound import playsound
from tts.engines import edge, speechify
from blingfire import text_to_sentences
from tts.voices import VOICES
from common.logger import logger
from itertools import count

class TTSManager:
    def __init__(self, max_concurrent_tasks: int = 10) -> None:
        self.engines = {
            "EdgeTTS": edge.EdgeTTS(),
            "SpeechifyTTS": speechify.SpeechifyTTS()
        }
        self.audio_queue = Queue(maxsize=50)
        self.semaphore = Semaphore(max_concurrent_tasks)
        self.futures = []  # List to hold futures for each sentence
        self.index_counter = count()  # Initialize the counter

    async def play_audio_async(self, mp3_file: str) -> None:
        if os.path.exists(mp3_file):
            try:
                await asyncio.to_thread(playsound, mp3_file)
                os.remove(mp3_file)
            except Exception as e:
                logger.error(f"Failed to play audio '{mp3_file}': {e}", exc_info=True)
        else:
            logger.error(f"Audio file not found: {mp3_file}")

    def cleanup(self, mp3_file: str) -> None:
        if os.path.exists(mp3_file):
            os.remove(mp3_file)

    def split_and_yield_sentences_genexpr(self, response) -> Generator[Tuple[int, str, asyncio.Future], None, None]:
        sentences = text_to_sentences(response)
        split_sentences = [s.strip() for s in sentences.split('\n') if s.strip()]
        futures = [asyncio.get_event_loop().create_future() for _ in split_sentences]
        self.futures.extend(futures)
        for index, (sentence, future) in enumerate(zip(split_sentences, futures)):
            logger.success(f"Split sentence {index}: {sentence}")
            yield index, sentence, future

    async def generate_audio_files(self, index: int, sentence: str, voice: str, engine, future: asyncio.Future) -> None:
        async with self.semaphore:
            try:
                mp3_file = await engine.generate_audio_with_retry(sentence, voice)
                future.set_result(mp3_file)
            except Exception as e:
                logger.error(f"Exception for index {index}: {e}", exc_info=True)
                future.set_exception(e)

    async def generate_and_play_audio(self, response: str, voice_name: str = "Ava_Edge") -> None:
        tasks = []
        VOICE = VOICES.get(voice_name)
        if not VOICE:
            logger.error(f"Voice '{voice_name}' not found. Using default 'Ana'.")
            VOICE = VOICES["Ava_Edge"]
        logger.success(f"Using voice '{VOICE.name}' and engine '{VOICE.engine}'")
        engine = VOICE.engine
        voice = VOICE.name
        engine_instance = self.engines.get(engine, self.engines["EdgeTTS"])

        try:
            # Use synchronous generator
            for index, sentence, future in self.split_and_yield_sentences_genexpr(response):
                task = create_task(self.generate_audio_files(index, sentence, voice, engine_instance, future))
                tasks.append(task)

            # Play audio in order by awaiting each future sequentially
            for i, future in enumerate(self.futures):
                try:
                    mp3_file = await future
                    await self.play_audio_async(mp3_file)
                except Exception as e:
                    logger.error(f"Error generating audio for sentence {i}: {e}")
                    # Optionally, decide how to handle the error (e.g., skip, retry, or stop)
            
            # Ensure all tasks are completed
            await gather(*tasks)
        except Exception as e:
            logger.error(f"Error occurred: {e}", exc_info=True)
            for task in tasks:
                task.cancel()
        finally:
            self.futures = []

if __name__ == "__main__":
    import asyncio
    tts = TTSManager()
    async def main():
        await tts.generate_and_play_audio(
            "EdgeTTS is ready to assist you. Here's the second paragraph. "
            "It contains several sentences to verify that the module splits and processes them correctly."
        )
    
    asyncio.run(main())

from faster_whisper import WhisperModel
from typing import Union
from pathlib import Path
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor
import gc
from src.utils.config import FASTER_WHISPER_MODELS_DIR
from src.utils.logger import setup_logging

class WhisperEngine:
    def __init__(self, model_path: str | Path = FASTER_WHISPER_MODELS_DIR):
        """
        Initialize WhisperEngine with a Whisper model.
        
        Args:
            model_path: Directory path where models will be stored
        """
        self.model_path = Path(model_path)
        self.model = None
        self.logger = None
        self._thread_pool = ThreadPoolExecutor(max_workers=1)  # Single worker to prevent OOM

    def normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalize audio data to float32 in range [-1, 1].
        Handles both int16 and float32 input formats.
        """
        if audio_data.dtype == np.int16:
            return audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.float32:
            return np.clip(audio_data, -1, 1)
        else:
            self.logger.error(f"Unsupported audio dtype: {audio_data.dtype}")
            raise ValueError(f"Unsupported audio dtype: {audio_data.dtype}")

    async def transcribe_audio(
        self,
        audio_data: np.ndarray
    ) -> str:
        """
        Transcribe audio data directly without saving to disk.
        
        Args:
            audio_data: Audio samples as numpy array (int16 or float32)
            sample_rate: Sampling rate of the audio (default: 16000)
            model_name: Model to use for transcription (default: "small")
            
        Returns:
            str: Transcribed text
        """
        self.logger.debug("Transcribing audio...")
        try:
            # Normalize audio to float32 in range [-1, 1]
            audio_normalized = self.normalize_audio(audio_data)
            
            # Get the selected model
            model = self.model
            
            # Run transcription in thread pool to avoid blocking
            segments, _ = await asyncio.get_event_loop().run_in_executor(
                self._thread_pool,
                lambda: model.transcribe(
                    audio_normalized,
                    beam_size=1,        # Reduce beam size for faster inference
                    best_of=1,          # Only return best result
                    language="en"       # Specify language for better accuracy
                )
            )
            # Join all segments and clean up the text
            return " ".join(segment.text for segment in segments).strip()
            
        except Exception as e:
            self.logger.error(f"Error in transcription: {e}")
            return ""
    async def transcribe_file(self, audio_path: Union[str, Path]) -> str:
        """
        Transcribe audio from a file path (kept for backward compatibility).
        
        Args:
            audio_path: Path to the audio file
            model_name: Model to use for transcription
            
        Returns:
            str: Transcribed text
        """
        model = self.model
        segments, _ = await asyncio.get_event_loop().run_in_executor(
            self._thread_pool,
            lambda: model.transcribe(
                str(audio_path),
                beam_size=1,
                best_of=1,
                language="en"
            )
        )
        return " ".join(segment.text for segment in segments).strip()

    async def __aenter__(self):
        """Async context manager entry."""
        self.logger = setup_logging()
        import time 
        start_time = time.time()
        # Your initialization logic here
        self.model = await asyncio.to_thread(
            lambda: WhisperModel(
                "small.en",
                download_root=self.model_path,
                compute_type="int8"
            )
        )
        self.logger.debug(f"Initialization took {time.time() - start_time:.2f} seconds")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Cleanup resources on exit.
        """
        self.logger.info("Exiting Whisper engine...")
        self._thread_pool.shutdown(wait=False)
        del self.model
        gc.collect()
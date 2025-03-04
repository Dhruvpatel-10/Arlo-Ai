import pvporcupine
import sounddevice as sd
import numpy as np
import os
import platform
import asyncio
from typing import List, Optional, Callable
from threading import Lock
from src.utils.logger import setup_logging
from src.wake_word.wake_manager import WakeWordCommand
from src.utils.config import WAKE_WORD_DIR
from src.core.error import AccessKeyError

class WakeWordDetector:
    def __init__(self, 
                 sensitivity: float = 0.5, 
                 buffer_size: int = 1024,
                 callback: Optional[Callable[[str], None]] = None):
        """
        Initialize wake word detector with Porcupine
        
        Args:
            access_key (str): Picovoice access key
            sensitivity (float): Detection sensitivity (0-1)
            buffer_size (int): Audio buffer size for processing
            callback (Optional[Callable]): Callback function when wake word is detected
        """
        
        self.sensitivity = sensitivity
        self.buffer_size = buffer_size
        self.callback = callback
        self.keyword_paths = self._load_model()
        
        self.porcupine = None
        self.audio_stream = None
        self.is_running = False
        self.detection_lock = Lock()
        
        # Pre-allocate numpy arrays for better performance
        self.audio_buffer = np.zeros(self.buffer_size, dtype=np.int16)
        
        # Map indices to wake word commands directly
        self.keyword_map = {
            0: WakeWordCommand.WAKE,
            1: WakeWordCommand.STOP,
            2: WakeWordCommand.PAUSE,
            3: WakeWordCommand.CONTINUE
        }
        self.logger = setup_logging()
        ACCESS_KEY = os.getenv("PICOV_ACCESS_KEY")
        if not ACCESS_KEY:
            raise AccessKeyError("PICOV_ACCESS_KEY is not set")
        self.access_key = ACCESS_KEY
        # Initialize Porcupine
        self._initialize_porcupine()

    def _initialize_porcupine(self):
        """Initialize or reinitialize the Porcupine instance"""
        if self.porcupine is not None:
            self.porcupine.delete()
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=self.keyword_paths,
                sensitivities=[self.sensitivity] * len(self.keyword_paths)
            )
        except AccessKeyError as e:
            print("AccessKeyError:", e)
            raise
       
    def _load_model(self) -> List[str]:
        """Load wake word model paths based on OS"""
        OS = platform.system().lower()
        return [
            str(WAKE_WORD_DIR / f"{OS}/Hey-Arlo_en_{OS}_v3_0_0.ppn"),
            str(WAKE_WORD_DIR / f"{OS}/Stop-Arlo_en_{OS}_v3_0_0.ppn"),
            str(WAKE_WORD_DIR / f"{OS}/Arlo-pause_en_{OS}_v3_0_0.ppn"),
            str(WAKE_WORD_DIR / f"{OS}/Arlo-continue_en_{OS}_v3_0_0.ppn")
        ]
    async def process_audio_chunk(self, chunk) -> bool:
        """Process a single audio chunk"""
        if len(chunk) == self.porcupine.frame_length:
            with self.detection_lock:
                keyword_index = self.porcupine.process(chunk)
                
                if keyword_index >= 0:
                    command = self.keyword_map.get(keyword_index)
                    if command and self.callback:
                        self.logger.info(f"Detected wake word command: {command.value}")
                        # Handle both async and non-async callbacks
                        if asyncio.iscoroutinefunction(self.callback):
                            await self.callback(command.value)
                        else:
                            self.callback(command.value)
                    return True
        return False

    async def audio_callback(self, indata, frames, time, status):
        """Process audio frame and detect wake words with optimized buffering"""
        if status:
            return
        
        np.copyto(self.audio_buffer[:frames], indata.flatten())
        
        for i in range(0, frames, self.porcupine.frame_length):
            chunk = self.audio_buffer[i:i + self.porcupine.frame_length]
            detected = await self.process_audio_chunk(chunk)
            if detected:
                return

    async def start_detection(self):
        """Start real-time audio detection asynchronously"""
        try:
            # Ensure Porcupine is initialized
            if self.porcupine is None:
                self._initialize_porcupine()
                
            self.is_running = True

            self.audio_stream = sd.InputStream(
                channels=1,
                samplerate=self.porcupine.sample_rate,
                dtype=np.int16,
                blocksize=self.buffer_size,
                latency='low'
            )
            
            with self.audio_stream:
                while self.is_running:
                    try:
                        indata, _ = self.audio_stream.read(self.buffer_size)
                        await self.audio_callback(indata, self.buffer_size, None, None)
                        await asyncio.sleep(0.01)  # Small sleep to prevent CPU hogging
                    except KeyboardInterrupt:
                        print("Exiting...")
        except Exception as e:
            self.logger.error(f"Error in wake word detection: {str(e)}")
            await self.cleanup()

    async def stop_detection(self):
        """Stop the detection process"""
        await self.restart_detection()

    async def restart_detection(self):
        """Restart the detection process"""
        self.is_running = False
        self.audio_stream = None

    async def cleanup(self):
        """Clean up resources asynchronously"""
        if self.audio_stream is not None:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
        if hasattr(self, 'porcupine') and self.porcupine is not None:
            self.porcupine.delete()
            self.porcupine = None
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
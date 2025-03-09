import sounddevice as sd
import numpy as np
import asyncio
import time
from typing import Optional, Dict, Any
from src.wake_word.vad import VADManager
from src.core.event_bus import EventBus, EventPriority
from src.utils.logger import setup_logging
from collections import deque


class AudioRecorder:
    """
    A self-contained async audio recording class with integrated VAD and pre-roll buffer. It subscribe to 'handle_recording' event.
    """
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: np.dtype = np.int16,
        blocksize: int = 512,
        device: int = None,
        pre_roll_duration: float = 2,  # Duration in seconds to keep in pre-roll buffer
        max_queue_size: int = 10  # Maximum number of utterances to keep in queue
    ):
        """Initialize the AudioRecorder with VADManager."""
        self.event_bus = event_bus
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.blocksize = blocksize
        self.device = device
        self.max_queue_size = max_queue_size
        
        self.logger = None
        self.audio_fetch_event = asyncio.Event()
        self.is_recording = False  # Make this a public attribute
        self.audio_queue = asyncio.Queue(maxsize=max_queue_size)
        self.stream = None
        self.vad_manager = VADManager(pre_roll_duration=pre_roll_duration)
        
        # Use deque for pre-roll buffer
        self.pre_roll_size = int(pre_roll_duration * sample_rate)
        self.pre_roll_buffer = deque(maxlen=self.pre_roll_size)
        
        # Use dynamic list for audio buffer
        self.current_buffer = []
        
        self._lock = asyncio.Lock()
        self._processing_task = None


    async def initialize(self):
        start_time = time.time()
        self.logger = setup_logging()
        self.event_bus.subscribe(
            "audio.record.request", 
            self._handle_recording, 
            priority=EventPriority.HIGH, 
            async_handler=True
        )
        # Your initialization logic here
        self.logger.debug(f"Initialization took {time.time() - start_time:.2f} seconds")

    async def shutdown(self):
        if self.is_recording:
            await self.stop_recording()

    async def _audio_callback(self, indata: np.ndarray) -> None:
        """Process audio data asynchronously."""
        async with self._lock:
            audio_data = indata.flatten()
            
            # Update pre-roll buffer using deque
            self.pre_roll_buffer.extend(audio_data)
            
            frame_length = self.vad_manager.cobra.frame_length
            for i in range(0, len(audio_data), frame_length):
                chunk = audio_data[i:i+frame_length]
                if len(chunk) == frame_length:
                    vad_state = await self.vad_manager.process_audio(chunk)
                    await self._handle_vad_state(vad_state, chunk)

    async def _handle_vad_state(self, vad_state: Dict[str, Any], chunk: np.ndarray) -> None:
        """Handle VAD state changes and audio buffering."""
        if vad_state['speech_started']:
            self.logger.info("VAD: Speech detected, starting recording.")
            await self._cleanup_old_data()
            
            # Convert pre-roll buffer to numpy array and start new recording
            self.current_buffer = list(self.pre_roll_buffer)
            self.is_recording = True
        
        if self.is_recording:
            self.current_buffer.extend(chunk)
        
        if vad_state['speech_ended']:
            self.logger.info(f"VAD: Speech ended after {vad_state['speech_duration']}s")
            self.is_recording = False
            
            if self.current_buffer:
                final_audio = np.array(self.current_buffer, dtype=self.dtype)
                try:
                    await self.audio_queue.put(final_audio)
                    self.audio_fetch_event.set()
                except asyncio.QueueFull:
                    self.logger.warning("Audio queue full, dropping oldest recording")
                    try:
                        await self.audio_queue.get()
                        await self.audio_queue.put(final_audio)
                    except asyncio.QueueEmpty:
                        pass
                finally:
                    self.current_buffer = []

    async def _process_audio_stream(self):
        """Continuously process audio stream."""
        while self.is_recording:
            try:
                indata, _ = self.stream.read(self.blocksize)
                await self._audio_callback(indata)
                await asyncio.sleep(0.001)  # Small sleep to prevent CPU hogging
            except Exception as e:
                self.logger.error(f"Error processing audio stream: {e}")
                await self.stop_recording()
                break
    
    async def start_recording(self):
        """Start recording with pre-roll buffer asynchronously."""
        if self.is_recording:
            return
        self.audio_fetch_event.clear()
        self.logger.info("Waiting for speech...")
        self.is_recording = True
        self.pre_roll_buffer.clear()
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=self.blocksize,
            device=self.device
        )
        self.stream.start()
        
        self._processing_task = asyncio.create_task(self._process_audio_stream())

    async def stop_recording(self):
        """Stop recording asynchronously."""
        self.logger.info("Stopping recording...")
        if not self.is_recording:
            return
        
        await self.vad_manager.reset()

        self.is_recording = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    async def _handle_recording(self):
        """Handle recording process."""   
        await self.start_recording()
        await self.audio_fetch_event.wait()
        await self.stop_recording()
            
    async def get_audio_data(self) -> Optional[np.ndarray]:
        """Retrieve recorded audio from the queue asynchronously."""
        if self.audio_fetch_event.is_set() and not self.audio_queue.empty():
            self.audio_fetch_event.clear()
            return await self.audio_queue.get()
        return None
    
    async def _cleanup_old_data(self):
        """Clean up old data to prevent memory growth."""
        while self.audio_queue.qsize() > self.max_queue_size - 1:
            try:
                await self.audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

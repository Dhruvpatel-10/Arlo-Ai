import sounddevice as sd
import numpy as np
import asyncio
from src.wake_word.vad import VADManager
from typing import Optional, Dict, Any
from src.utils.logger import setup_logging


class AudioRecorder:
    """A self-contained async audio recording class with integrated VAD and pre-roll buffer."""
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: np.dtype = np.int16,
        blocksize: int = 512,
        device: int = None,
        pre_roll_duration: float = 2,  # Duration in seconds to keep in pre-roll buffer
        max_queue_size: int = 10  # Maximum number of utterances to keep in queue
    ):
        """Initialize the AudioRecorder with VADManager."""
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.blocksize = blocksize
        self.device = device
        self.max_queue_size = max_queue_size
        
        self.logger = None
        
        self.is_recording = False  # Make this a public attribute
        self.audio_queue = asyncio.Queue(maxsize=max_queue_size)
        self.stream = None
        self.vad_manager = VADManager(pre_roll_duration=pre_roll_duration)
        
        # Calculate pre-roll buffer size in samples
        self.pre_roll_size = int(pre_roll_duration * sample_rate)
        self.pre_roll_buffer = np.zeros(self.pre_roll_size, dtype=self.dtype)
        self.pre_roll_index = 0
        
        # Use numpy array for audio buffer with pre-allocated size
        self.max_audio_buffer_size = int(sample_rate * 30)  # Max 30 seconds per utterance
        self.audio_buffer = np.zeros(self.max_audio_buffer_size, dtype=self.dtype)
        self.audio_buffer_index = 0
        self.utterance_ready = False
        
        self._lock = asyncio.Lock()
        self._processing_task = None

    async def _audio_callback(self, indata: np.ndarray) -> None:
        """Process audio data asynchronously."""
        async with self._lock:
            audio_data = indata.flatten()
            
            # Update pre-roll buffer
            samples_to_write = len(audio_data)
            space_remaining = self.pre_roll_size - self.pre_roll_index
            
            if samples_to_write >= space_remaining:
                self.pre_roll_buffer[:-samples_to_write] = self.pre_roll_buffer[samples_to_write:]
                self.pre_roll_buffer[-samples_to_write:] = audio_data
                self.pre_roll_index = self.pre_roll_size
            else:
                self.pre_roll_buffer[self.pre_roll_index:self.pre_roll_index + samples_to_write] = audio_data
                self.pre_roll_index += samples_to_write
                
                if self.pre_roll_index >= self.pre_roll_size:
                    self.pre_roll_index = 0
            
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
            self.audio_buffer_index = 0
            
            # Copy pre-roll buffer
            pre_roll_data = self.pre_roll_buffer.copy()
            self.audio_buffer[:len(pre_roll_data)] = pre_roll_data
            self.audio_buffer_index = len(pre_roll_data)
            self.is_recording = True
        
        if self.is_recording:
            if self.audio_buffer_index + len(chunk) >= self.max_audio_buffer_size:
                self.logger.warning("Audio buffer full, stopping recording")
                self.is_recording = False
                return
            
            self.audio_buffer[self.audio_buffer_index:self.audio_buffer_index + len(chunk)] = chunk
            self.audio_buffer_index += len(chunk)
        
        if vad_state['speech_ended']:
            self.logger.info(f"VAD: Speech ended after {vad_state['speech_duration']}s")
            self.is_recording = False
            final_audio = self.audio_buffer[:self.audio_buffer_index].copy()
            
            try:
                await self.audio_queue.put(final_audio)
                self.utterance_ready = True
            except asyncio.QueueFull:
                self.logger.warning("Audio queue full, dropping oldest recording")
                try:
                    await self.audio_queue.get()
                    await self.audio_queue.put(final_audio)
                except asyncio.QueueEmpty:
                    pass

    async def _process_audio_stream(self):
        """Continuously process audio stream."""
        while self.is_recording:
            try:
                indata, _ = self.stream.read(self.blocksize)
                await self._audio_callback(indata)
                await asyncio.sleep(0.001)  # Small sleep to prevent CPU hogging
            except Exception as e:
                self.logger.error(f"Error processing audio stream: {e}")
                break

    async def start_recording(self):
        """Start recording with pre-roll buffer asynchronously."""
        if self.is_recording:
            return

        self.logger.info("Waiting for speech...")
        self.is_recording = True
        self.pre_roll_buffer.fill(0)
        self.pre_roll_index = 0
        
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

    async def get_audio_data(self) -> Optional[np.ndarray]:
        """Retrieve recorded audio from the queue asynchronously."""
        if self.utterance_ready and not self.audio_queue.empty():
            self.utterance_ready = False
            return await self.audio_queue.get()
        return None

    async def clear_queue(self):
        """Clear the audio queue asynchronously."""
        while not self.audio_queue.empty():
            try:
                await self.audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def _cleanup_old_data(self):
        """Clean up old data to prevent memory growth."""
        while self.audio_queue.qsize() > self.max_queue_size - 1:
            try:
                await self.audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def __aenter__(self):
        """Async context manager entry."""
        self.logger = setup_logging()
        import time
        start_time = time.time()
        # Your initialization logic here
        self.logger.debug(f"Initialization took {time.time() - start_time:.2f} seconds")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.is_recording:
            await self.stop_recording()

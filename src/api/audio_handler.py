import sounddevice as sd
import numpy as np
from typing import Optional
import asyncio
import queue
from src.utils.logger import setup_logging

class AudioHandler:
    def __init__(self, event_bus):
        self.logger = setup_logging(module_name="Audio_Handler")
        self.event_bus = event_bus
        self.stream: Optional[sd.InputStream] = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_duration = 0.1  # seconds
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        # Buffer for accumulating audio chunks
        self.audio_buffer = []
        self.buffer_threshold = 20  # Number of chunks to accumulate (2 seconds)

        # Start the queue processing task
        asyncio.create_task(self._process_audio_queue())

    async def start_recording(self):
        """Start recording audio"""
        if self.is_recording:
            self.logger.warning("Already recording")
            return

        try:
            self.is_recording = True
            self.audio_buffer = []  # Clear buffer on start
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16,
                blocksize=self.chunk_size,
                callback=self._audio_callback
            )
            self.stream.start()
            self.logger.info("Started recording")
        except Exception as e:
            self.logger.error(f"Error starting recording: {e}")
            await self.event_bus.publish(
                topic_name="error",
                data=f"Failed to start recording: {str(e)}"
            )
            self.is_recording = False

    def stop_recording(self):
        """Stop recording audio"""
        if not self.is_recording:
            self.logger.warning("Not recording")
            return

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            self.is_recording = False
            # Add any remaining buffer to queue
            if self.audio_buffer:
                combined_audio = np.concatenate(self.audio_buffer)
                self.audio_queue.put_nowait(combined_audio.tobytes())
                self.audio_buffer = []
            self.logger.info("Stopped recording")
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio data - runs in a separate thread"""
        if status:
            self.logger.warning(f"Audio callback status: {status}")
            return

        if self.is_recording:
            try:
                # Add chunk to buffer
                self.audio_buffer.append(indata.copy())
                
                # If buffer is full, combine and send
                if len(self.audio_buffer) >= self.buffer_threshold:
                    combined_audio = np.concatenate(self.audio_buffer)
                    self.audio_queue.put_nowait(combined_audio.tobytes())
                    self.audio_buffer = []  # Clear buffer
                    
            except queue.Full:
                self.logger.warning("Audio queue is full, dropping chunk")
            except Exception as e:
                self.logger.error(f"Error in audio callback: {e}")

    async def _process_audio_queue(self):
        """Process audio chunks from the queue - runs in the event loop"""
        while True:
            try:
                # Check queue size and log if it's getting too large
                if self.audio_queue.qsize() > 10:
                    self.logger.warning(f"Audio queue size: {self.audio_queue.qsize()}")

                # Non-blocking get with timeout
                try:
                    audio_data = self.audio_queue.get_nowait()
                    if audio_data:
                        await self.event_bus.publish(
                            topic_name="audio.transcribe",
                            data={"audio_data": audio_data}
                        )
                except queue.Empty:
                    pass  # Queue is empty, that's fine

                # Small sleep to prevent busy waiting
                await asyncio.sleep(0.01)
            except Exception as e:
                self.logger.error(f"Error processing audio queue: {e}")
                await asyncio.sleep(1)  # Longer sleep on error 
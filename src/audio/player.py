import numpy as np
import asyncio
import sounddevice as sd
from src.utils.logger import setup_logging

logger = setup_logging()

async def play_audio_async(self, audio_data: np.ndarray, samplerate: int) -> None:
    """Plays audio with pause & resume support."""
    try:
        self.stop_flag.clear()  # Reset stop flag
        num_samples = len(audio_data)

        # Continue from last position if resuming
        start_pos = self.last_playback_position.get(self.next_index_to_play, 0)
        stream = sd.OutputStream(samplerate=samplerate, channels=1, dtype='float32')
        
        with stream:
            while start_pos < num_samples:
                if self.stop_flag.is_set():
                    logger.info("Playback stopped.")
                    self.last_playback_position[self.next_index_to_play] = 0  # Reset position
                    return

                while not self.pause_event.is_set():
                    await asyncio.sleep(0.1)  # Wait while paused
                
                # Process small chunks to allow interruption
                chunk_size = 1024  # Adjust for responsiveness
                end_pos = min(start_pos + chunk_size, num_samples)

                stream.write(audio_data[start_pos:end_pos])
                start_pos = end_pos
                self.last_playback_position[self.next_index_to_play] = start_pos  # Save position

        # Reset position when fully played
        self.last_playback_position[self.next_index_to_play] = 0

    except Exception as e:
        logger.error(f"Failed to play audio: {e}", exc_info=True)
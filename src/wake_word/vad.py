import pvcobra
import platform
import os
import time
import numpy as np
import asyncio
from typing import Dict, Any
from src.utils.config import VAD_LINUX_DIR, VAD_WIN_DIR

class VADManager:
    """Voice Activity Detection manager using Picovoice Cobra."""
    def __init__(
        self,
        speech_timeout: float = 1.2,
        min_speech_length: float = 0.1,
        vad_threshold: float = 0.64,
        pre_roll_duration: float = 0.5
    ):
        """Initialize VAD manager."""
        if platform.system() == 'Linux': 
            library_path = VAD_LINUX_DIR
        elif platform.system() == 'Windows': 
            library_path = VAD_WIN_DIR
        else: 
            raise OSError("Unsupported operating system")
        
        access_key = os.getenv("PICOV_ACCESS_KEY")
        self.cobra = pvcobra.Cobra(access_key=access_key, library_path=library_path)
                
        self.speech_timeout = speech_timeout
        self.min_speech_length = min_speech_length
        self.vad_threshold = vad_threshold
        self.pre_roll_duration = pre_roll_duration
        
        self.speech_detected = False
        self.speech_start_time = None
        self.last_speech_time = None
        self.is_final_silence = False
        self._lock = asyncio.Lock()

    async def process_audio(self, audio_frame: np.ndarray) -> Dict[str, Any]:
        """Process audio frame and detect voice activity asynchronously."""
        async with self._lock:
            current_time = time.time()
            vad_confidence = self.cobra.process(audio_frame)
            
            vad_state = {
                'is_speech': vad_confidence >= self.vad_threshold,
                'speech_started': False,
                'speech_ended': False,
                'vad_confidence': vad_confidence,
                'speech_duration': 0.0
            }
            
            if vad_state['is_speech']:  # Speech detected
                if not self.speech_detected:
                    self.speech_detected = True
                    self.speech_start_time = current_time
                    vad_state['speech_started'] = True
                self.last_speech_time = current_time
                self.is_final_silence = False
                
            elif self.speech_detected:  # Detect silence after speech
                silence_duration = current_time - self.last_speech_time
                if silence_duration >= self.speech_timeout and not self.is_final_silence:
                    self.is_final_silence = True
                    speech_duration = current_time - self.speech_start_time
                    if speech_duration >= self.min_speech_length:
                        vad_state['speech_ended'] = True
                        vad_state['speech_duration'] = speech_duration
                        self.speech_detected = False
            
            return vad_state

    async def reset(self):
        """Reset VAD state asynchronously."""
        async with self._lock:
            self.speech_detected = False
            self.speech_start_time = None
            self.last_speech_time = None
            self.is_final_silence = False

    async def cleanup(self):
        """Cleanup resources asynchronously."""
        if hasattr(self, 'cobra'):
            self.cobra.delete()
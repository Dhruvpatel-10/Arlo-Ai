# src/tts/base_tts.py
from abc import ABC, abstractmethod
from typing import Optional
import asyncio

class TTSEngine(ABC):
    @abstractmethod
    async def generate_audio(self, text: str) -> Optional[str]:
        pass
    
    @abstractmethod
    async def generate_audio_with_retry(self, text: str, retries: int = 3, retry_delay: float = 0.7) -> Optional[str]:
        attempt = 0
        while attempt < retries:
            audio_file = await self.generate_audio(text)
            if audio_file:
                return audio_file
            attempt += 1
            if attempt < retries:
                await asyncio.sleep(retry_delay)
        return None

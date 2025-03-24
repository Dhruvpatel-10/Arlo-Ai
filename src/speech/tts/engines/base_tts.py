# src/tts/base_tts.py
from abc import ABC, abstractmethod
from typing import Optional

class TTSEngine(ABC):
    @abstractmethod
    async def generate_audio(self, text: str) -> Optional[str]:
        pass

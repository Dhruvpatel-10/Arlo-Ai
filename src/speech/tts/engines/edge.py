import os
import asyncio
from typing import Optional
from src.speech.tts.engines.base_tts import TTSEngine
from src.utils.logger import setup_logging
from src.utils.config import AUDIO_DIR
from src.utils.helpers import GenericUtils
import aiofiles
import edge_tts

logger = setup_logging()

class EdgeTTS(TTSEngine):
    @GenericUtils.retry
    async def generate_audio(self, text: str, voice="en-US-AvaNeural", InModule=False) -> Optional[bytes]:
        try:
            # Create communicate object
            communicate = edge_tts.Communicate(text, voice)
            
            # Generate audio data
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            if audio_data:
                logger.info(f"EdgeTTS generated audio for text: {text[:50]}...")
                return audio_data
            else:
                logger.error("EdgeTTS failed to generate audio data")
                return None
                
        except Exception as e:
            logger.error(f"EdgeTTS encountered an error: {e}")
            return None

if __name__ == "__main__":
    tts = EdgeTTS()
    paragraph = '''
    Sonali Bendre spotted with fractured hand at the airport: 'Toot Gaya Haath
    '''.strip()
    async def main():
        await tts.generate_audio(text=paragraph, InModule=True)
        
    asyncio.run(main())
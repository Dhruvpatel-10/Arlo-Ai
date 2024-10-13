import os
import aiohttp
import asyncio
import base64
from typing import Optional
from tts.engines.base_tts import TTSEngine
from src.common.logger import logger
from src.common.config import AUDIO_DIR
import aiofiles

class SpeechifyTTS(TTSEngine):  
    async def generate_audio(self, text: str,voice="sophia") -> Optional[str]:
        logger.success(f"SpeechifyTTS generating audio for: {text}")
        unique_id = int.from_bytes(os.urandom(8), 'big')
        mp3_file = os.path.join(AUDIO_DIR, f"Speechify_{unique_id}.mp3")
        url = "https://audio.api.speechify.com/generateAudioFiles"
        payload = {
            "audioFormat": "mp3",
            "paragraphChunks": [text],
            "voiceParams": {
                "name": voice,
                "engine": "speechify",
                "languageCode": "en-US"
            }
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()
                    json_response = await response.json()
                    audio_data = base64.b64decode(json_response['audioStream'])
                    async with aiofiles.open(mp3_file, 'wb') as audio_file:
                        await audio_file.write(audio_data)
                    logger.success(f"SpeechifyTTS audio generated: {mp3_file}")
                    return mp3_file
        except Exception as e:
            logger.error(f"SpeechifyTTS failed to generate audio: {e}")
            return None
        
    async def generate_audio_with_retry(self, text: str, voice:str) -> Optional[str]:
        retries: int = 3
        retry_delay: float = 0.7
        attempt = 0
        while attempt < retries:
            audio_file = await self.generate_audio(text,voice)
            if audio_file:
                return audio_file
            attempt += 1
            if attempt < retries:
                await asyncio.sleep(retry_delay)
        return None

    
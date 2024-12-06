import aiohttp
import asyncio
import base64
from typing import Optional
from src.tts.engines.base_tts import TTSEngine
from src.common.logger import setup_logging

logger = setup_logging()

class SpeechifyTTS(TTSEngine):
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.url = "https://audio.api.speechify.com/generateAudioFiles"

    async def __aenter__(self):
        await self.ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.info("Closing SpeechifyTTS")
        await self.close()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def generate_audio(self, text: str, voice="sophia") -> Optional[bytes]:
        logger.debug(f"SpeechifyTTS generating audio for: {text}")
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
            await self.ensure_session()
            async with self.session.post(self.url, json=payload) as response:
                response.raise_for_status()
                json_response = await response.json()
                audio_data = base64.b64decode(json_response['audioStream'])
                logger.info(f"SpeechifyTTS audio generated for text: {text}")
                return audio_data
        except Exception as e:
            logger.error(f"SpeechifyTTS failed to generate audio: {e}", exc_info=True)
            return None

    async def generate_audio_with_retry(self, text: str, voice: str) -> Optional[bytes]:
        retries: int = 3
        retry_delay: float = 0.7
        for attempt in range(retries):
            audio_data = await self.generate_audio(text, voice)
            if audio_data:
                return audio_data
            if attempt < retries - 1:
                logger.warning(f"Retrying SpeechifyTTS audio generation for text: {text} (Attempt {attempt + 2})")
                await asyncio.sleep(retry_delay)
        return None

if __name__ == "__main__":
    tts = SpeechifyTTS()
    audio_data = asyncio.run(tts.generate_audio_with_retry("Hello, how are you?", "jamie"))
    # print(audio_data)
    with open("test.mp3", "wb") as f:
        f.write(audio_data)
    


import aiohttp
import asyncio
import base64
from typing import Optional
from src.speech.tts.engines.base_tts import TTSEngine
from src.utils.logger import setup_logging
from src.utils.helpers import retry

logger = setup_logging()

class SpeechifyTTS(TTSEngine):
    def __init__(self):
        self.url = "https://audio.api.speechify.com/generateAudioFiles"

    @retry
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
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload) as response:
                    response.raise_for_status()
                    json_response = await response.json()
                    audio_data = base64.b64decode(json_response['audioStream'])
                    logger.info(f"SpeechifyTTS audio generated for text: {text}")
                    return audio_data
        except Exception as e:
            logger.error(f"SpeechifyTTS failed to generate audio: {e}", exc_info=True)
            return None

if __name__ == "__main__":
    tts = SpeechifyTTS()
    audio_data = asyncio.run(tts.generate_audio_with_retry("Hello, how are you?", "jamie"))
    if audio_data:
        with open("test.mp3", "wb") as f:
            f.write(audio_data)
    


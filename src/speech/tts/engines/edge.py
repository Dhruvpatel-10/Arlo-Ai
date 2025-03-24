import os
import asyncio
from typing import Optional
from src.speech.tts.engines.base_tts import TTSEngine
from src.utils.logger import setup_logging
from src.utils.config import AUDIO_DIR
from src.utils.helpers import retry
import aiofiles

logger = setup_logging()

class EdgeTTS(TTSEngine):

    @retry
    async def generate_audio(self, text: str, voice="en-US-AvaNeural", InModule=False) -> Optional[bytes]:
        unique_id = int.from_bytes(os.urandom(8), 'big')
        temp_f = os.path.join(AUDIO_DIR, f'temp_text_{unique_id}.txt')
        mp3_file = os.path.join(AUDIO_DIR, f"EdgeTTS_{unique_id}.mp3")
        try:
            # Write the text to a temporary file
            async with aiofiles.open(temp_f, 'w', encoding='utf-8') as f:
                await f.write(text)
            
            # Generate the audio file using the edge-tts command
            command = [
                'edge-tts',
                '--voice', voice,
                '--file', temp_f,
                '--write-media', mp3_file,
                '--rate=+5%',
            ]
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stderr = await asyncio.wait_for(process.communicate(), timeout=30)
                if process.returncode == 0 and os.path.exists(mp3_file):
                    # Read the generated MP3 file into bytes
                    async with aiofiles.open(mp3_file, 'rb') as audio_file:
                        audio_data = await audio_file.read()
                    return audio_data
                else:
                    error_msg = stderr.strip() if stderr else "Unknown error."
                    logger.error(f"EdgeTTS failed: {error_msg}")
                    return None

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logger.error("EdgeTTS command timed out.")
                return None
        except Exception as e:
            logger.error(f"EdgeTTS encountered an error: {e}")
            return None
        finally:
            # Clean up temporary files
            if os.path.exists(temp_f):
                try:
                    os.remove(temp_f)
                except Exception as e:
                    logger.error(f"Error deleting temporary file {temp_f}: {e}")
            if os.path.exists(mp3_file) and InModule == False:
                try:
                    os.remove(mp3_file)
                except Exception as e:
                    logger.error(f"Error deleting audio file {mp3_file}: {e}")

if __name__ == "__main__":
    tts = EdgeTTS()
    paragraph = '''Paragraphs are the building blocks of papers. Many students define paragraphs in terms of length: a paragraph is a group of at least five sentences, a paragraph is half a page long, etc. In reality, though, the unity and coherence of ideas among sentences is what constitutes a paragraph. A paragraph is defined as “a group of sentences or a single sentence that forms a unit” (Lunsford and Connors 116). Length and appearance do not determine whether a section in a paper is a paragraph. For instance, in some styles of writing, particularly journalistic styles, a paragraph can be just one sentence long. Ultimately, a paragraph is a sentence or group of sentences that support one main idea. In this handout, we will refer to this as the “controlling idea,” because it controls what happens in the rest of the paragraph.'''
    async def main():
        audio_file = await tts.generate_audio(text=paragraph, InModule=True)
        print(audio_file)

    asyncio.run(main())
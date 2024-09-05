
from ..TTS.tts import generate_audio, play_audio_sequence

def split_text_into_paragraphs(text):
    paragraphs = text.split('\n\n')
    return [para.strip() for para in paragraphs if para.strip()]

def combine_last_two_paragraphs(paragraphs):
    if len(paragraphs) > 1:
        paragraphs[-2] = paragraphs[-2] + ' ' + paragraphs[-1]
        paragraphs.pop()
    return paragraphs
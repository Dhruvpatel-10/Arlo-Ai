import os
from audio.stop_word import play_audio

def speak(text: str, voice: str = 'en-IE-EmilyNeural', subtitle_file: str = 'Subtitles_File.srt') -> None:
    text = os.linesep.join([s.strip() for s in text.splitlines() if s.strip()])

    command = f"edge-tts --voice \"{voice}\" --text \"{text}\" --write-media \"{voice}.mp3\" --write-subtitles {subtitle_file}"

    os.system(command)
    play_audio(f"{voice}.mp3")
    os.remove(subtitle_file)
    os.remove(f"{voice}.mp3")

if __name__ == "__main__": 
    speak("The sun sets slowly over the ocean, painting the sky with hues of orange and pink, as the sound of waves crashing against the shore fills the air.")

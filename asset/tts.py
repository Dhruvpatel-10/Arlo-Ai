import os
from audio.stop_word import play_audio

def speak(text: str, voice: str = 'en-US-AvaNeural') -> None:
    
    input_file = "asset/g/output_audio.mp3"
    subtitle_file = 'asset/g/Subtitles_File.srt' 
    command = f"edge-tts --voice \"{voice}\" --text \"{text}\" --write-media \"{input_file}\" --write-subtitles {subtitle_file}"
    
    os.system(command)
    play_audio(input_file)
    os.remove(subtitle_file)
    os.remove(input_file)

if __name__ == "__main__": 
    speak("Despite the serendipitous encounter, the indomitable scientist remained staunchly resolute in her preliminary hypothesis.")


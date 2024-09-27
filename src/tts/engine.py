import os
from random import randint
import subprocess
from playsound import playsound
from src.common.config import AUDIO_DIR

def generate_audio(text: str, voice: str = "en-US-AvaNeural") -> str:
    # Clean and format text
    limited_hash = randint(0, 145269)
    text = os.linesep.join([s.strip().replace("*", "") for s in text.splitlines() if s.strip()])

    # Create directory for audio files
    dir_path = AUDIO_DIR
    os.makedirs(dir_path, exist_ok=True)

    # Define paths for unique temporary files
    temp_f = os.path.join(dir_path, f'temp_text_{limited_hash}.txt')
    mp3_file = os.path.join(dir_path, f"genAudio_{limited_hash}.mp3")

    try:
        # Write text to unique temporary file
        with open(temp_f, 'w', encoding='utf-8') as f:
            f.write(text)

        # Generate MP3 using edge-tts
        command = [
            'edge-tts',
            '--voice', voice,
            '--file', temp_f,
            '--write-media', mp3_file
        ]
        
        # Execute the command and capture output for debugging
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print(f"Error generating audio for text '{text}':\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)

    finally:
        # Clean up temporary text file
        if os.path.exists(temp_f):
            os.remove(temp_f)

    return mp3_file

def play_audio(mp3_file: str) -> None:
    if os.path.exists(mp3_file):
        try:
            playsound(mp3_file)
            os.remove(mp3_file)
        except Exception as e:
            print(f"Failed to play the audio: {e}")
    else:
        print(f"File not found: {mp3_file}")

def play_audio_sequence(mp3_files: list) -> None:
    # Play a sequence of audio files
    for mp3_file in mp3_files:
        play_audio(mp3_file)

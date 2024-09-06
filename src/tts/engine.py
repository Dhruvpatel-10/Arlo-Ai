import os
import subprocess
from random import randint 
import sounddevice as sd
import soundfile as sf


def generate_audio(text: str, voice: str, audio_dir: str) -> str:
    # Clean and format text
    limited_hash = randint(0, 10001)
    text = os.linesep.join([s.strip().replace("*", "") for s in text.splitlines() if s.strip()])

    # Create directory for audio files
    dir_path = os.path.join(os.path.dirname(__file__), audio_dir)
    os.makedirs(dir_path, exist_ok=True)

    # Define paths for temporary files
    temp_f = os.path.join(dir_path, 'temp_text.txt')
    mp3_file = os.path.join(dir_path, f"{voice}_{limited_hash}.mp3")

    # Write text to temporary file
    with open(temp_f, 'w', encoding='utf-8') as f:
        f.write(text)

    # Generate MP3 using edge-tts
    command = f'edge-tts --voice "{voice}" --file "{temp_f}" --write-media "{mp3_file}"'
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Clean up temporary text file
    if os.path.exists(temp_f): os.remove(temp_f)
    return mp3_file

def play_audio(mp3_file: str) -> None:
    if os.path.exists(mp3_file):
        try:
            # Read audio data from the file
            data, samplerate = sf.read(mp3_file)
            
            # Play the audio file using sounddevice
            sd.play(data, samplerate)
            sd.wait()  # Wait until the file is finished playing
            
            # Optionally remove the audio file after playing
            os.remove(mp3_file)
        except Exception as e:
            print(f"Failed to play the audio: {e}")
    else:
        print(f"File not found: {mp3_file}")

def play_audio_sequence(mp3_files: list) -> None:
    # Play a sequence of audio files
    for mp3_file in mp3_files:
        play_audio(mp3_file)

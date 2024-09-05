import os
import subprocess
import hashlib
import sounddevice as sd
import soundfile as sf

def generate_limited_hash(text, range_max=100):
    # Generate a hash from the text
    hash_object = hashlib.md5(text.encode())
    hash_bytes = hash_object.digest()
    
    # Convert the first byte of the hash to an integer
    hash_int = hash_bytes[0]
    
    # Limit the hash value to the range 1-range_max
    limited_hash = (hash_int % range_max) + 1
    
    return limited_hash

def generate_audio(text: str, voice: str, audio_dir: str) -> str:
    # Clean and format text
    limited_hash = generate_limited_hash(text)
    text = os.linesep.join([s.strip().replace("*","") for s in text.splitlines() if s.strip()])

    # Create directory for audio files
    dir_path = os.path.join(os.path.dirname(__file__), audio_dir)
    os.makedirs(dir_path, exist_ok=True)

    subtitle_file = os.path.join(dir_path, 'Subtitles_File.srt') 

    # Write text to temporary file
    temp_f = os.path.join(dir_path, 'temp_text.txt')
    with open(temp_f, 'w', encoding='utf-8') as f:
        f.write(text)

    # Define output audio file path
    mp3_file = os.path.join(dir_path, f"{voice}_{limited_hash}.mp3")

    # Generate audio using edge-tts
    command = f'edge-tts --voice "{voice}" --file "{temp_f}" --write-media "{mp3_file}" --write-subtitles "{subtitle_file}"'
    subprocess.run(command, shell=True, check=True)

    os.remove(temp_f)
    os.remove(subtitle_file)

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

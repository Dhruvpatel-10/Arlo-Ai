import os
import subprocess
from audio.stop_word import play_audio

def speak(text: str, voice: str = 'en-US-AvaNeural', subtitle_file: str = 'Subtitles_File.srt') -> None:
    # Normalize line endings and remove extra whitespace
    text = os.linesep.join([s.strip().replace("**", "") for s in text.splitlines() if s.strip()])


    # Define the directory for the temp files
    dir_path = os.path.dirname(__file__) 
    temp_f = os.path.join(dir_path, 'temp_text.txt')
    
    # Create a temporary file to store the text
    with open(temp_f, 'w', encoding='utf-8') as f:
        f.write(text)
    
    # Paths for MP3 and subtitle files
    mp3_file = os.path.join(dir_path, f"{voice}.mp3")
    subtitle_path = os.path.join(dir_path, subtitle_file)

    # Check if the MP3 file already exists, if so, delete it
    if os.path.exists(mp3_file): 
        os.remove(mp3_file)

    # Check if the subtitle file already exists, if so, delete it
    if os.path.exists(subtitle_path):
        os.remove(subtitle_path)

    # Construct the command using the text file
    command = f'edge-tts --voice "{voice}" --file "{temp_f}" --write-media "{mp3_file}" --write-subtitles "{subtitle_path}"'

    # Execute the command using subprocess
    subprocess.run(command, shell=True, check=True)

    # Play the generated audio
    play_audio(mp3_file)

    # Clean up by deleting the files after use
    os.remove(temp_f)
    if os.path.exists(subtitle_path):
        os.remove(subtitle_path)
    if os.path.exists(mp3_file):
        os.remove(mp3_file)


if __name__ == "__main__":
    speak('''The sun sets slowly over the ocean, painting the sky with hues of orange and pink, as the sound of waves crashing against the shore fills the air.
1. Hey this is good 
2. Thank you''')

    

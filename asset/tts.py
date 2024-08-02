import requests
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from typing import Union

def generate_audio(message: str, voice: str = "Brian"):
    url = f"https://api.streamelements.com/kappa/v2/speech?voice={voice}&text={{{message}}}"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        result = requests.get(url=url, headers=headers)
        return result.content
    except:
        return None
    
def speak(message: str, voice: str = "Brian", folder: str = "asset", extension: str = ".mp3") -> Union[None, str]:
    file_path = os.path.join(folder, f"{voice}{extension}")
    try:
        result_content = generate_audio(message, voice)

        # Check if the file already exists and delete it
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Save the new audio file
        with open(file_path, "wb") as file:
            file.write(result_content)
        
        # Initialize pygame mixer and play the audio
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        # Wait until the audio is finished playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)  # Add a small delay to prevent high CPU usage

        # Stop and uninitialize the mixer
        pygame.mixer.music.stop()
        pygame.mixer.quit()

        return None
    except Exception as e:
        return "Error playing TTS: " + str(e)
    finally:
        # Ensure the file is deleted after execution
        if os.path.exists(file_path):
            os.remove(file_path)
    
if __name__ == "__main__": 
    speak("Thank you for watching! I hope you found this video informative and helpful. If you did, please give it a thumbs up and consider subscribing to my channel for more videos like this", voice="Salli")

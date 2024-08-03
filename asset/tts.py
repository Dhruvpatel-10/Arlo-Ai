import requests
import base64
from audio.stop_word import play_audio
import os

def speak(text: str, model: str = "aura-luna-en", filename: str = "asset\output_audio.mp3"):
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass

    url = "https://deepgram.com/api/ttsAudioGeneration"
    payload = {"text": text, "model": model}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() 

        with open(filename, 'wb') as audio_file:
            audio_file.write(base64.b64decode(response.json()['data']))

        play_audio(filename)
        os.remove(filename)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}") 
    except Exception as err:
        print(f"An error occurred: {err}")  

if __name__ == "__main__":
    speak("Thank you for watching! I hope you found this video informative and helpful. If you did, please give it a thumbs up and consider subscribing to my channel for more videos like this")

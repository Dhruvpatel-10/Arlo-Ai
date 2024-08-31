import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import threading
import time

try: from audio.hotword_detection import HotwordDetector
except ModuleNotFoundError: from hotword_detection import HotwordDetector
except: raise Exception("Failed to import Hotword_Detection module.")

def play_audio_Event(file_path: str, stop_event: threading.Event, prints: bool = False) -> None:
  
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    if prints: print(f"Playing audio: {file_path}")
    
    while pygame.mixer.music.get_busy() and not stop_event.is_set():
        time.sleep(0.1)  
    
    if stop_event.is_set():
        pygame.mixer.music.stop()
        if prints: print("Audio playback stopped.")
    
    pygame.mixer.quit()
    if prints: print("Pygame mixer quit.")

def detect_hotword(detector: HotwordDetector, stop_event: threading.Event, prints: bool = False) -> None:
    
    hotword_detected = detector.listen_for_hotwords()
    if hotword_detected:
        stop_event.set()
        if prints: print("Hotword detected, Setting Stop Event.")

def play_audio(audio_file_path: str = "asset\output_audio.mp3", prints: bool = False) -> None:
    stop_event = threading.Event()
    detector = HotwordDetector()

    audio_thread = threading.Thread(target=play_audio_Event, args=(audio_file_path, stop_event, prints))
    hotword_thread = threading.Thread(target=detect_hotword, args=(detector, stop_event, prints))

    audio_thread.start()
    hotword_thread.start()

    audio_thread.join()
    detector.stop()
    hotword_thread.join()

    if prints: print("Application exited gracefully.")

if __name__ == "__main__":
    audio_file_path = 'asset/output_audio.mp3'
    play_audio(audio_file_path)
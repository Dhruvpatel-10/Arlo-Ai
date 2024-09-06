from src.llm.model import *
from src.llm.utils import *
from tts.audio import generate_audio_files
from common.config import IMAGES_DIR
import queue

def main():
    print("\n[INFO] Initializing Assistant...")
    while True:
        user_prompt = input("\nUSER: ")
        call = function_call(user_prompt)
        visual_context = None
        imgpath = IMAGES_DIR
        if 'take screenshot' in call:
            print('\n[INFO] Taking screenshot...')
            take_screenshot()
            visual_context = vision_prompt(prompt=user_prompt, photo_path=os.path.join(imgpath, 'screenshot.jpg'))
                
        elif 'capture webcam' in call:
            print('\n[INFO] Capturing webcam...')
            web_cam_capture()
            visual_context = vision_prompt(prompt=user_prompt, photo_path=os.path.join(imgpath, 'webcam.jpg'))
                
        elif 'extract clipboard' in call:
            print('\n[INFO] Extracting clipboard text...')
            clipboard_text = get_clipboard_text()
            if clipboard_text:
                user_prompt = f'{user_prompt}\n\nCLIPBOARD CONTENT: {clipboard_text}'
                visual_context = None

        response = groq_prompt(prompt=user_prompt, img_context=visual_context)
        print("\n" + "="*50)
        print(f"ASSISTANT: {response}")
        print("="*50)
        text_queue = queue.Queue()
        paragraphs = split_and_combine_text(response)
        for para in paragraphs:
            text_queue.put(para)    
        generate_audio_files(text_queue)
    
import os
from common.config import IMAGES_DIR
import cv2
import pyperclip as pc
from PIL import ImageGrab, Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai_api = os.getenv("GEMINI_API")
genai.configure(api_key=genai_api)
web_cam = cv2.VideoCapture(0)
dir_path = IMAGES_DIR

generation_config = {
    'temperature': 0.7,
    'top_p': 1,
    'top_k': 1,
    'max_output_tokens': 2048
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel('gemini-1.5-flash-latest',
                              generation_config=generation_config,
                              safety_settings=safety_settings)

def take_screenshot():
    path = os.path.join(dir_path, 'screenshot.jpg')
    screenshot = ImageGrab.grab()
    rgb_screenshot = screenshot.convert('RGB')
    rgb_screenshot.save(path, quality=15)

def web_cam_capture():
    global web_cam
    if not web_cam.isOpened():
        print('Error: Camera did not open successfully')
        web_cam = cv2.VideoCapture(0) 
        if not web_cam.isOpened():
            print('Error: Camera could not be reinitialized')
            return
    path = os.path.join(dir_path, 'webcam.jpg')
    ret, frame = web_cam.read()
    if ret:
        cv2.imwrite(path, frame)
        print('Webcam image captured successfully.')
    else:
        print('Error: Failed to capture image')
    
    web_cam.release()
    cv2.destroyAllWindows()
    web_cam = cv2.VideoCapture(0)

def get_clipboard_text():
    clipboard_content = pc.paste()
    if isinstance(clipboard_content, str):
        return clipboard_content
    else:
        print('No clipboard text to copy')
        return None
    
def vision_prompt(prompt, photo_path) -> str:
    img = Image.open(photo_path)
    vision_prompt_text = (
        f'You are the vision analysis AI that provides semantic meaning from images to provide context '
        f'to send to another AI that will create a response to the user. Do not respond as the AI assistant '
        f'to the user. Instead, take the user prompt input and try to extract all meaning from the photo '
        f'relevant to the user prompt. Then generate as much objective data about the image for the AI '
        f'assistant who will respond to the user. \nUSER PROMPT: {prompt}'
    )
    response = model.generate_content([vision_prompt_text, img])
    os.remove(photo_path)
    return response.text
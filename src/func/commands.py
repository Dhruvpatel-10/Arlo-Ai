import os
import cv2
import pyperclip as pc
from PIL import ImageGrab, Image
import google.generativeai as genai
from dotenv import load_dotenv
import subprocess
import webbrowser
from common.config import IMAGES_DIR

# Load environment variables
load_dotenv()
genai_api = os.getenv("GEMINI_API")
genai.configure(api_key=genai_api)

# Initialize webcam
web_cam = cv2.VideoCapture(0)
dir_path = IMAGES_DIR

# Generation configuration for AI
generation_config = {
    'temperature': 0.7,
    'top_p': 1,
    'top_k': 1,
    'max_output_tokens': 2048
}

# Safety settings for AI model
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Initialize the AI model
model = genai.GenerativeModel('gemini-1.5-flash-latest',
                              generation_config=generation_config,
                              safety_settings=safety_settings)

# Function to take a screenshot
def take_screenshot():
    path = os.path.join(dir_path, 'screenshot.jpg')
    screenshot = ImageGrab.grab()
    rgb_screenshot = screenshot.convert('RGB')
    rgb_screenshot.save(path, quality=15)

# Function to capture image from webcam
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

# Function to get text from clipboard
def get_clipboard_text():
    clipboard_content = pc.paste()
    if isinstance(clipboard_content, str):
        return clipboard_content
    else:
        print('No clipboard text to copy')
        return None

# Function to generate a vision prompt
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

# Functions to open various applications
def open_word():
    try:
        subprocess.Popen(['start', 'winword'], shell=True)
        return "Microsoft Word opened successfully."
    except Exception as e:
        return f"Error opening Microsoft Word: {str(e)}"

def open_excel():
    try:
        subprocess.Popen(['start', 'excel'], shell=True)
        return "Microsoft Excel opened successfully."
    except Exception as e:
        return f"Error opening Microsoft Excel: {str(e)}"

def open_powerpoint():
    try:
        subprocess.Popen(['start', 'powerpnt'], shell=True)
        return "Microsoft PowerPoint opened successfully."
    except Exception as e:
        return f"Error opening Microsoft PowerPoint: {str(e)}"

def open_browser(url='https://www.google.com'):
    try:
        webbrowser.open(url)
        return f"Opened {url} in the default browser."
    except Exception as e:
        return f"Error opening the browser: {str(e)}"

def open_youtube(search_query=None):
    base_url = "https://www.youtube.com"
    if search_query:
        search_url = f"{base_url}/results?search_query={search_query.replace(' ', '+')}"
    else:
        search_url = base_url
    return open_browser(search_url)

# Main assistant function to process commands
def process_command(command):
    command = command.lower()
    if "open word" in command:
        return open_word()
    elif "open excel" in command:
        return open_excel()
    elif "open powerpoint" in command:
        return open_powerpoint()
    elif "open youtube" in command:
        if "search" in command:
            search_query = command.split("search")[-1].strip()
            return open_youtube(search_query)
        else:
            return open_youtube()
    elif "open browser" in command or "open google" in command:
        return open_browser()
    else:
        return "I'm sorry, I didn't understand that command."
    
if __name__ == '__main__':
    pass

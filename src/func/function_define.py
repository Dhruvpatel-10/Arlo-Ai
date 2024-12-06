import os
import cv2
import pyperclip as pc
from PIL import ImageGrab, Image
import base64 
from groq import Groq
import subprocess
from common.config import IMAGES_DIR
from common.logger import setup_logging
import webbrowser
import sys
import base64

api_key = os.getenv("GROQ_VISION_API")
client = Groq(api_key= api_key)
logger = setup_logging()

# Initialize webcam
web_cam = cv2.VideoCapture(0)
dir_path = IMAGES_DIR

# Function to take a screenshot
def take_screenshot():
    if sys.platform == 'linux':
        path = os.path.join(dir_path, 'screenshot.jpg')
        screenshot = ImageGrab.grab()
        rgb_screenshot = screenshot.convert('RGB')
        rgb_screenshot.save(path, quality=15)
        return path
    else:
        # Define the file path for the screenshot
        raw_path = os.path.join(dir_path, "raw_screenshot.png")  # Temporary PNG file
        final_path = os.path.join(dir_path, "screenshot.jpg")    # Compressed final file

        # Take the screenshot using gnome-screenshot
        subprocess.run(["gnome-screenshot", "-f", raw_path])  # Save as PNG

        # Open the PNG, convert to RGB, and save as compressed JPEG
        with Image.open(raw_path) as img:
            img = img.convert("RGB")  # Ensure it's in RGB mode
            img.save(final_path, quality=15)  # Save with reduced quality

        # Optionally, delete the temporary PNG file
        # os.remove(raw_path)
        return final_path

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
    return path

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
    vision_prompt_text = (f'''You are a vision analysis AI designed to extract semantic information from images, focusing on screenshots and webcam captures. Your goal is to provide concise, detailed descriptions that include:
    1. Exact text in the image
    2. Contextual elements and their significance
    3. Screen contents, interface details, and composition
    4. Relevant metadata or insights

    Generate a neutral, single-paragraph description that highlights key elements relevant to the user's query, providing context for another AI to craft a final response. Avoid assumptions or irrelevant details; focus only on factual, observable information directly related to the prompt. USER PROMPT: {prompt}''')
    
    logger.debug(f"{dir_path} photo path: {photo_path}")
    
    with open(photo_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    chat_completion = client.chat.completions.create(
    messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text":vision_prompt_text},
                {
                    "type": "image_url",
                    "image_url": {

                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                },
            ],
        }
    ],
    model="llama-3.2-90b-vision-preview",
)
    # os.remove(photo_path)
    return chat_completion.choices[0].message.content

def open_word():
    try:
        # Using subprocess to open Microsoft Word
        subprocess.Popen(['start', 'winword'], shell=True)
        return "Microsoft Word opened successfully."
    except FileNotFoundError:
        return "Microsoft Word executable not found. Please check if Word is installed."
    except Exception as e:
        return f"Error opening Microsoft Word: {str(e)}"

def open_excel():
    try:
        subprocess.Popen(['start', 'excel'], shell=True)
        return "Microsoft Excel opened successfully."
    except FileNotFoundError:
        return "Microsoft Excel executable not found. Please check if Excel is installed."
    except Exception as e:
        return f"Error opening Microsoft Excel: {str(e)}"

def open_powerpoint():
    try:
        subprocess.Popen(['start', 'powerpnt'], shell=True)
        return "Microsoft PowerPoint opened successfully."
    except FileNotFoundError:
        return "Microsoft PowerPoint executable not found. Please check if PowerPoint is installed."
    except Exception as e:
        return f"Error opening Microsoft PowerPoint: {str(e)}"

def handle_browser(url):
    try:
        webbrowser.open(url)
        return f"{url} opened successfully."
    except Exception as e:
        return f"Error opening browser: {str(e)}"
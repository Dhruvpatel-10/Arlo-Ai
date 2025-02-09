import os
import cv2
import pyperclip as pc
from PIL import Image
import base64 
from groq import Groq
import subprocess
from common.config import IMAGES_DIR, VISION_LLM_MODEL
from common.logger import setup_logging
import webbrowser


api_key = os.getenv("GROQ_VISION_API")
client = Groq(api_key= api_key)
logger = setup_logging()

# Initialize webcam
dir_path = IMAGES_DIR

# Function to take a screenshot
def take_screenshot():      
    try:
        import mss
        use_mss = True
    except ImportError:
        use_mss = False

    try:
        import pyscreenshot
        use_pyscreenshot = True
    except ImportError:
        use_pyscreenshot = False

    quality = 95
    scale = 1.0
    max_size_mb=1
    screenshot = None
    min_quality=60
    min_scale=0.5
    output_path = os.path.join(dir_path, 'screenshot.jpg')

    # Try capturing with mss first
    if use_mss:
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                sct_img = sct.grab(monitor)
                screenshot = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
        except Exception as e:
            print(f"mss failed: {e}, falling back to pyscreenshot.")

    # Fallback to pyscreenshot if mss failed or unavailable
    if screenshot is None and use_pyscreenshot:
        try:
            screenshot = pyscreenshot.grab().convert('RGB')
        except Exception as e:
            print(f"pyscreenshot failed: {e}. No screenshot method available.")
            return None

    if screenshot is None:
        print("No screenshot method available.")
        return None

    orig_width, orig_height = screenshot.size

    # Optimize size
    while True:
        img = (screenshot.resize((int(orig_width * scale), int(orig_height * scale)),
                                  Image.Resampling.LANCZOS)
               if scale < 1.0 else screenshot).convert('RGB')

        img.save(output_path, 'JPEG', quality=quality)
        size_mb = os.path.getsize(output_path) / (1024 * 1024)

        if size_mb <= max_size_mb:
            break

        # Reduce quality first, then scale down if needed
        if quality > min_quality:
            quality = max(quality - 5, min_quality)
        elif scale > min_scale:
            scale *= 0.9
        else:
            print(f"Could not reduce file size below {max_size_mb}MB")
            break

    print(f"Screenshot saved: {output_path} ({size_mb:.2f}MB, quality={quality}, scale={scale:.2f})")
    return output_path


# Function to capture image from webcam
def web_cam_capture():
    camera_indices=[0, 1, -1]
    image_path = os.path.join(dir_path, 'webcam.jpg')

    # Iterate over the provided camera indices
    for idx in camera_indices:
        print(f"Trying camera index: {idx}")
        cap = None
        try:
            cap = cv2.VideoCapture(idx)
            if not cap.isOpened():
                print(f"Warning: Camera index {idx} could not be opened.")
                continue  # Try next index

            # Try to capture a valid frame
            for attempt in range(5):
                ret, frame = cap.read()
                if ret and frame is not None:
                    try:
                        cv2.imwrite(image_path, frame)
                        print(f"Image captured successfully from camera index {idx} and saved at: {image_path}")
                        cap.release()
                        return image_path
                    except Exception as e:
                        print(f"Error saving image from camera index {idx}: {e}")
                        cap.release()
                        return False
                else:
                    print(f"Attempt {attempt + 1}: Failed to capture a valid frame from camera index {idx}.")
            print(f"Error: No valid frame captured from camera index {idx} after multiple attempts.")
        except Exception as e:
            print(f"Exception while accessing camera index {idx}: {e}")
        finally:
            if cap is not None:
                cap.release()
    
    print("Error: Could not capture image from any of the provided camera indices.")
    return False

# Function to get text from clipboard
def get_clipboard_text():
    clipboard_content = pc.paste()
    if isinstance(clipboard_content, str):
        logger.info(f"CLIPBOARD CONTENT: {clipboard_content}")
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
        base64_size = (os.path.getsize(photo_path) * 4) // 3 
        logger.debug(f"Base64 size: {base64_size / 1024:.2f} KB")

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
    model=VISION_LLM_MODEL,
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
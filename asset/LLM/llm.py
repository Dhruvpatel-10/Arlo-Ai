import os
from groq import Groq
from PIL import ImageGrab, Image
import google.generativeai as genai
import cv2
import pyperclip as pc
from dotenv import load_dotenv
import re

load_dotenv()
groq_api = os.getenv("GROQ_API")
genai_api = os.getenv("GEMINI_API")
groq_client = Groq(api_key=groq_api)
genai.configure(api_key=genai_api)
web_cam = cv2.VideoCapture(0)
dir_path = os.path.dirname(__file__)



sys_msg = (
    '''You are Lexi, a sweet and humorous voice assistant. Your user may provide a photo (screenshot or webcam capture) for context. This photo has been processed into a detailed text prompt, which will be combined with their voice input. Generate clear, factual, and concise responses based on all provided context. Use the conversation history effectively and avoid requesting additional images. Keep your responses brief and engaging, fitting for a voice assistant.'''
)


convo = [{"role": "system", "content": sys_msg}]

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

def groq_prompt(prompt, img_context):
    if img_context:
        prompt = f'USER PROMPT: {prompt}\nIMAGE CONTEXT: {img_context}'
    convo.append({"role": "user", "content": prompt})
    chat_completion = groq_client.chat.completions.create(model="llama3-70b-8192", messages=convo)
    response = chat_completion.choices[0].message
    convo.append(response)
    response_text = response.content 
    if not isinstance(response_text, str):
        raise ValueError("Input must be a string.")
    text = re.sub(r'\*\*', '', response_text)  
    response_text = re.sub(r'\*', '', text) 
    return response_text

def function_call(prompt):
    sys_msg = (
        '''You are responsible for choosing one action from this list: ["extract clipboard", "take screenshot", "capture webcam", "None"]. Only choose "capture webcam" if the user explicitly mentions needing the camera or visual input. Use "extract clipboard" only if the user references copied text or content. Choose "take screenshot" if there is a clear reference to screen content. If none of these conditions apply, return "None". Respond with only the function name.'''
    )
    function_convo = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": prompt}
    ]
    chat_completion = groq_client.chat.completions.create(messages=function_convo, model="llama3-70b-8192")
    response = chat_completion.choices[0].message
    return response.content

def take_screenshot():
    path = os.path.join(dir_path, 'images\screenshot.jpg')
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
    path = os.path.join(dir_path, 'images\webcam.jpg')
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



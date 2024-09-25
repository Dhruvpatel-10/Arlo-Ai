import os
# from func.vision_func import take_screenshot, web_cam_capture, get_clipboard_text, vision_prompt
from src.llm.model import groq_prompt
from src.llm.utils import split_and_combine_text
from tts.audio import generate_audio_files
from common.config import IMAGES_DIR
from collections import deque
from func.commands import process_command
from func.function_registry import FunctionRegistry, HybridFunctionCaller
from dotenv import load_dotenv
from groq import Groq
load_dotenv()

groq_api = os.getenv("GROQ_API_FUNC")

groq_client = Groq(api_key=groq_api)
registry = FunctionRegistry()
function_caller = HybridFunctionCaller(registry)

def main():
    print("\n[INFO] Initializing Assistant...")
    while True:
        user_prompt = input("\nUSER: ")
        # Call the hybrid function to determine the action
        action = function_caller.call(user_prompt)
        action = str(action)
        f_exe = None
        visual_context = None
        if action != "None":
            f_exe, visual_context = process_command(action)
        response = groq_prompt(prompt=user_prompt, img_context=visual_context, function_execution=f_exe)

        print("\n" + "="*50)
        print(f"ASSISTANT: {response}")
        print("="*50)

        # Generate audio response from the text response
        text_queue = deque()
        paragraphs = split_and_combine_text(response)
        for para in paragraphs:
            text_queue.append(para) 
        generate_audio_files(text_queue)

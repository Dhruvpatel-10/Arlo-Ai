from collections import deque
from src.llm.model import groq_prompt
from src.llm.utils import split_and_combine_text
from tts.audio import generate_audio_files_multiprocessing
from func.cmdpharser import process_command
from func.function_registry import FunctionRegistry, HybridFunctionCaller
from src.url.url_parser import SearchQueryFinder
from src.common.logger import logger
def main():
    print("\n[INFO] Initializing Assistant...")
    registry = FunctionRegistry()
    function_caller = HybridFunctionCaller(registry)
    search_query = SearchQueryFinder()
    while True:
        user_prompt = input("\nUSER: ")
        # Call the hybrid function to determine the action
        if user_prompt == "exit":
            break
        action = function_caller.call(user_prompt)
        action = str(action)
        f_exe = None
        visual_context = None
        if action != "None":
            if 'open_browser':
                 logger.info("OPENING BROWSER")
                 Url_parser = search_query.find_query(prompt=user_prompt)
                 f_exe, visual_context = process_command(command=action,url=Url_parser)
                 logger.info(f"f_exe: {f_exe} and visual_context: {visual_context}")
            else:
                logger.info("PROCESSING COMMAND")
                f_exe, visual_context = process_command(command=action, user_prompt=user_prompt)
                logger.info(f"f_exe: {f_exe} and visual_context: {visual_context}")
        response = groq_prompt(prompt=user_prompt, img_context=visual_context, function_execution=f_exe)

        print("\n" + "="*50)
        print(f"ASSISTANT: {response}")
        print("="*50)

        # Generate audio response from the text response
        text_queue = deque()
        paragraphs = split_and_combine_text(response)
        for para in paragraphs:
            text_queue.append(para) 
        generate_audio_files_multiprocessing(text_queue)

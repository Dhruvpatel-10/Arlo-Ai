from multiprocessing import Queue
from src.llm.model import groq_prompt
from src.llm.utils import split_and_combine_text
from tts.audio import start_audio_processes
from func.cmdpharser import process_command
from func.function_registry import FunctionRegistry, HybridFunctionCaller
from src.url.url_parser import SearchQueryFinder
from src.common.logger import logger, signal_handler, delete_af , revlog
from src.common.config import load_history
import signal

signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signal

def main():
    print("\n[INFO] Initializing Assistant...")
    logger.warning("Initializing Assistant...")
    delete_af()
    history = load_history()
    registry = FunctionRegistry()
    function_caller = HybridFunctionCaller(registry)
    search_query = SearchQueryFinder()
    text_queue = Queue(maxsize=100)
    audio_queue = Queue(maxsize=100)
    generator_process, player_process = start_audio_processes(text_queue, audio_queue)
    try:
        while True:
            user_prompt = input("\nUSER: ")
            # Call the hybrid function to determine the action
            if user_prompt.lower() == "exit" or user_prompt.lower() == "q":
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
            response = groq_prompt(prompt=user_prompt, img_context=visual_context, function_execution=f_exe, history=history)

            print("\n" + "="*50)
            print(f"ASSISTANT: {response}")
            print("="*50)

            # Generate audio response from the text response
            
            paragraphs = split_and_combine_text(response)
            if paragraphs:
                logger.info(f"Splitting response into {len(paragraphs)} paragraphs for audio generation.")
                for para in paragraphs:
                    logger.info(f"Sending text chunk to audio generator: {para[:30]}...")
                    text_queue.put(para)  
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt. Exiting.")

    finally:
        # Send sentinel values to terminate audio processes
        logger.info("Sending sentinel to audio generator.")
        text_queue.put(None)  # Signal the generator to terminate

        # Wait for processes to finish
        logger.info("Waiting for audio processes to finish.")
        generator_process.join()
        player_process.join()

        logger.info("All audio processes have finished. Terminating assistant.")
        # Terminate processes
        generator_process.terminate()
        player_process.terminate()

        # Close processes
        logger.info("Closing audio processes.")
        generator_process.close()
        player_process.close()
        signal_handler(signal.SIGINT, None)
        revlog()
        logger.info("Audio processes have been terminated. Goodbye!")
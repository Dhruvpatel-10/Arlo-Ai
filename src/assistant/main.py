# main.py
import sys
from queue import Queue
from src.llm.model import groq_prompt
from tts.audio import start_audio_threads
from func.cmdpharser import process_command
from func.function_registry import FunctionRegistry, HybridFunctionCaller
from src.url.url_parser import SearchQueryFinder
from src.common.logger import logger, delete_af, signal_handler
from src.common.config import load_history
import signal

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signal

def main():

    print("\n[INFO] Initializing Assistant...")
    logger.info("Initializing Assistant...")
    delete_af()
    history = load_history()
    registry = FunctionRegistry()
    function_caller = HybridFunctionCaller(registry)
    search_query = SearchQueryFinder()
    text_queue = Queue()
    audio_queue = Queue()
    threads = start_audio_threads(text_queue, audio_queue, pool_size=1)
    
    try:
        while True:
            user_prompt = input("\nUSER: ")
            if user_prompt.lower() in ["exit", "q"]:
                logger.info("Exit command received. Shutting down.")
                break
            
            action = function_caller.call(user_prompt)
            action = str(action)
            f_exe = None
            visual_context = None

            if action != "None":
                if 'open_browser' in action:
                    logger.info("OPENING BROWSER")
                    url_parser = search_query.find_query(prompt=user_prompt)
                    f_exe, visual_context = process_command(command=action, url=url_parser)
                    logger.info(f"f_exe: {f_exe} and visual_context: {visual_context}")
                else:
                    logger.info("PROCESSING COMMAND")
                    f_exe, visual_context = process_command(command=action, user_prompt=user_prompt)
                    logger.info(f"f_exe: {f_exe} and visual_context: {visual_context}")
            
            response = groq_prompt(prompt=user_prompt, img_context=visual_context, function_execution=f_exe, history=history)

            print("\n" + "="*50)
            print(f"ASSISTANT: {response}")
            print("="*50)

            try:
                logger.info(f"Sending text chunk to audio generator: {response[:30]}...")
                text_queue.put(response)  
            except Exception as e:
                logger.error(f"Error putting text chunk into queue: {e}")

    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt. Exiting.")
    finally:
        # Wait until all tasks are done
        logger.info("Waiting for all tasks in text_queue to be processed.")
        text_queue.join()
        logger.info("All tasks in text_queue have been processed.")
        logger.info("Waiting for all tasks in audio_queue to be processed.")
        audio_queue.join()
        logger.info("All tasks in audio_queue have been processed.")

        # Send sentinel values to terminate audio threads
        logger.info("Sending sentinel to audio threads.")
        for _ in threads:
            text_queue.put(None)  # Signal the generator threads to terminate

        # Wait for all threads to finish
        logger.info("Waiting for audio threads to finish.")
        for thread in threads:
            thread.join()
            logger.info(f"Joined thread: {thread.name}")
        
        logger.info("All audio threads have finished. Terminating assistant.")
        logger.info("Assistant terminated. Goodbye!")
        sys.exit()

if __name__ == "__main__":
    main()

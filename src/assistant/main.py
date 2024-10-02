from queue import Queue
from src.llm.model import groq_prompt
from src.llm.utils import split_and_enqueue_response 
from tts.audio import start_audio_threads
from func.cmdpharser import process_command
from func.function_registry import FunctionRegistry, HybridFunctionCaller
from src.url.url_parser import SearchQueryFinder
from src.common.logger import logger, delete_af, signal_handler
from src.common.config import load_history
import signal

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)  
signal.signal(signal.SIGTERM, signal_handler)

def main():
    print("\n[INFO] Initializing Assistant...")
    logger.info("Initializing Assistant...")
    delete_af()
    history = load_history()
    registry = FunctionRegistry()
    function_caller = HybridFunctionCaller(registry)
    search_query = SearchQueryFinder()
    text_queue = Queue(maxsize=100)
    audio_queue = Queue(maxsize=100)
    threads = start_audio_threads(text_queue, audio_queue, pool_size=2)
    
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

            if action and "none" not in action.lower():
                if 'open_browser' in action:
                    logger.info("OPENING BROWSER")
                    url_parser = search_query.find_query(prompt=user_prompt)
                    f_exe, visual_context = process_command(command=action, url=url_parser)
                else:
                    logger.info("PROCESSING COMMAND")
                    f_exe, visual_context = process_command(command=action, user_prompt=user_prompt)
                logger.info(f"f_exe: {f_exe} and visual_context: {visual_context}")
            
            response = groq_prompt(prompt=user_prompt, img_context=visual_context, function_execution=f_exe, history=history)

            print("\n" + "="*50)
            print(f"ASSISTANT: {response}")
            print("="*50)
            if len(response.split()) > 20:
                logger.info("Response too long. Splitting and enqueuing response.")
                split_and_enqueue_response(response, text_queue)
            else:
                logger.info("Less than 20 words. Enqueuing response.")
                text_queue.put(response)

    except KeyboardInterrupt:
        logger.error("Received KeyboardInterrupt. Exiting.")
    finally:
        # Clean up code (same as before)
        logger.info("Waiting for all tasks in text_queue to be processed.")
        text_queue.join()
        logger.info("All tasks in text_queue have been processed.")
        logger.info("Waiting for all tasks in audio_queue to be processed.")
        audio_queue.join()
        logger.info("All tasks in audio_queue have been processed.")

        logger.info("Sending sentinel to audio threads.")
        for _ in threads:
            text_queue.put(None)

        logger.info("Waiting for audio threads to finish.")
        for thread in threads:
            thread.join()
            logger.info(f"Joined thread: {thread.name}")
        
        logger.info("All audio threads have finished. Terminating assistant.")
        logger.info("Assistant terminated. Goodbye!")

if __name__ == "__main__":
    main()
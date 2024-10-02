# main.py
import asyncio
from asyncio import Queue, Event
import aioconsole

from src.llm.model import groq_prompt
from src.llm.utils import split_and_enqueue_response 
from tts.audio import start_audio_workers
from func.cmdpharser import process_command
from func.function_registry import FunctionRegistryAndCaller
from src.url.url_parser import SearchQueryFinder
from src.common.logger import logger, delete_af
import src.common.config as config

async def main():
    print("\n[INFO] Initializing Assistant...")
    logger.info("Initializing Assistant...")
    delete_af()
    
    function_caller = await FunctionRegistryAndCaller.create()
    search_query = SearchQueryFinder()
    text_queue = Queue(maxsize=100)
    audio_queue = Queue(maxsize=100)
    
    # Start audio workers
    workers = await start_audio_workers(text_queue, audio_queue, pool_size=2)
    
    shutdown_event = Event()
    
    async def user_input_loop():
        while not shutdown_event.is_set():
            try:
                user_prompt = await aioconsole.ainput("\nUSER: ")
            except (EOFError, KeyboardInterrupt):
                logger.info("User triggered exit.")
                shutdown_event.set()
                break
            if user_prompt.lower() in ["exit", "q"]:
                logger.info("Exit command received. Shutting down.")
                shutdown_event.set()
                break
            
            action = await function_caller.call(user_prompt)
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
            
            response = groq_prompt(prompt=user_prompt, img_context=visual_context, function_execution=f_exe)

            print("\n" + "="*50)
            print(f"ASSISTANT: {response}")
            print("="*50)
            
            if len(response.split()) > 20:
                logger.info("Response too long. Splitting and enqueuing response.")
                await split_and_enqueue_response(response, text_queue)
            else:
                logger.info("Less than 20 words. Enqueuing response.")
                async with config.index_lock:
                    current_index = config.global_index_counter
                    config.global_index_counter += 1
                logger.success(f"global_index_counter: {current_index}, Response: {response[:10]}")
                await text_queue.put((current_index, response))
                logger.info(f"global_index_counter: {config.global_index_counter}")

    try:
        await user_input_loop()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        # Initiate shutdown
        logger.info("Initiating shutdown sequence.")

        # Wait for queues to be processed
        logger.info("Sending sentinel to audio workers.")
        for _ in workers:
            await text_queue.put((None, None))  # Send sentinel to audio generators
            await audio_queue.put((None,None))
        logger.info("Waiting for audio workers to finish.")
        await asyncio.gather(*workers, return_exceptions=True)  # Wait for all workers to finish
        logger.info("Waiting for all tasks in text_queue to be processed.")
        await text_queue.join()
        logger.info("All tasks in text_queue have been processed.")
        logger.info("Waiting for all tasks in audio_queue to be processed.")
        await audio_queue.join()
        logger.info("All tasks in audio_queue have been processed.")

        # Send sentinel to audio workers

        # Wait for audio workers to finish
        
        logger.info("All audio workers have finished. Terminating assistant.")
        logger.info("Assistant terminated. Goodbye!")

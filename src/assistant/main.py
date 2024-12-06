# main.py
import aioconsole
from src.llm.model import groq_prompt
from func.cmdpharser import process_command
from func.function_registry import FunctionRegistryAndCaller
from src.url.url_parser import SearchQueryFinder
from src.tts.tts_manager import TTSManager
from src.common.logger import setup_logging, delete_af

async def main():
    logger = setup_logging()
    logger.info("Initializing assistant...")
    function_caller = await FunctionRegistryAndCaller.create()
    search_query = SearchQueryFinder()
    tts_manager = TTSManager()

    async def user_input_loop():
        while True:
            try:
                user_prompt = await aioconsole.ainput("\nUSER: ")
            except (EOFError, KeyboardInterrupt):
                logger.info("User triggered exit.")
                break
            if user_prompt.lower() in ["exit", "q"]:
                logger.info("Exit command received. Shutting down.")
                break

            action = await function_caller.call(user_prompt)
            action = str(action).lower()
            f_exe = None
            visual_context = None

            if action and "none" not in action.lower():
                if 'open_browser' in action:
                    logger.info("OPENING BROWSER")
                    url_parser = search_query.find_query(prompt=user_prompt)
                    f_exe, visual_context = process_command(command=action, url=url_parser)
                else:
                    logger.info("EXECUTING FUNCTION")
                    f_exe, visual_context = process_command(command=action, user_prompt=user_prompt)
                logger.info(f"f_exe: {f_exe} || visual_context: {visual_context}")

            response = groq_prompt(prompt=user_prompt, img_context=visual_context, function_execution=f_exe)

            print("\n" + "="*50)
            print(f"ASSISTANT: {response}")
            print("="*50)
            try:
                print("Playing Audio...")
                await tts_manager.generate_and_play_audio(response)
            except Exception as e:
                logger.error(f"Failed to play audio: {e}")            

    try:
        await user_input_loop()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        delete_af()
        await tts_manager.close_all_engines()
        
        # Initiate shutdown
        logger.info("Initiating shutdown sequence.")
        logger.info("Assistant terminated. Goodbye!")
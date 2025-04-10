# main.py
import asyncio
from src.llm.model import groq_prompt
from src.utils.shared_resources import EVENT_BUS, STATE_MANAGER
from src.core.state import  AssistantState
from src.audio.central_manager import CentralAudioManager
from src.url.url_parser import SearchQueryFinder
from src.utils.logger import setup_logging
from dotenv import load_dotenv
load_dotenv()
class Assistant:
    def __init__(self):
        self.event_bus = EVENT_BUS
        self.state_manager = STATE_MANAGER
        self.logger = None
        self.transcription = None
        self.classification = None
        self.central_manager = None
        self.search_query = None
        self.function_caller = None

    @classmethod
    async def create(cls):
        """Factory method to initialize the class asynchronously."""
        self = cls()  # Create instance
        
        # Initialize synchronous components
        self.logger = setup_logging(module_name="Assistant")

        # Initialize async components
        self.event_bus = EVENT_BUS
        self.state_manager = STATE_MANAGER

        # Create background tasks
        self.central_manager = await CentralAudioManager.create()
        self.search_query = SearchQueryFinder()
        await self.event_subscriber()
        
        # Don't start the user_input_loop here
        # Instead, return the instance so the caller can decide when to start it
        return self

    # Add a method to start processing
    async def start_processing(self):
        """Start the user input loop as a separate task."""
        return asyncio.create_task(self.user_input_loop())

    async def _get_result(self, transcript:str = None, classification:str = None) -> None:

        if transcript is not None:
            self.logger.info("Got the transcript")
            self.transcription = transcript

        if classification is not None:
            self.logger.info("Got the classification")
            self.classification = classification

    async def event_subscriber(self) -> None:

        self.event_bus.subscribe(
        topic_name="get.result", 
        callback=self._get_result, 
        async_handler=True
        )

    async def user_input_loop(self):
        while True:
            try:
                try:
                    await self.event_bus.publish("start.wakeword.detection")
                    await self.event_bus.publish("start.audio.recording")
                    user_prompt: str = self.transcription
                except (EOFError, KeyboardInterrupt):
                    self.logger.info("User triggered exit.")
                    break

                if user_prompt.strip().lower() in ["exit", "q"]:
                    self.logger.info("Exit command received. Shutting down.")
                    break

                if await self.state_manager.get_state() == AssistantState.IDLE:
                    continue

                await self.state_manager.set_state(AssistantState.PROCESSING)    

                # action = await self.function_caller.call(user_prompt)
                # action = str(action).lower()
                # f_exe = None
                # visual_context = None

                # if action and "none" not in action.lower():
                #     if 'open_browser' in action:
                #         self.logger.info("OPENING BROWSER")
                #         url_parser = self.search_query.find_query(prompt=user_prompt)
                #         f_exe, visual_context = process_command(command=action, url=url_parser)
                #     else:
                #         self.logger.info("EXECUTING FUNCTION")
                #         f_exe, visual_context = process_command(command=action, user_prompt=user_prompt)
                #     self.logger.info(f"f_exe: {f_exe} || visual_context: {visual_context}")
                print("== Reached groq promt ==")
                response = await groq_prompt(prompt=user_prompt, img_context=None, function_execution=None)
                await self.event_bus.publish("send.api",response=response)
                print("\n" + "="*50)
                print(f"ASSISTANT: {response}")
                print("="*50)
                
                try:
                    await self.event_bus.publish("start.tts.playback", response)
                except Exception as e:
                    self.logger.error(f"Failed to play audio: {e}")            
            
            except (EOFError, KeyboardInterrupt):
                self.logger.info("User triggered exit.")
            except Exception as e:
                self.logger.error(f"An unexpected error occurred: {e}")
        try:
            await self.user_input_loop()
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
        finally:
            await self.central_manager.shutdown()

            # Initiate shutdown
            self.logger.info("Initiating shutdown sequence.")
            self.logger.info("Assistant terminated. Goodbye!")
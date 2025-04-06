import asyncio

from src.tool_classifier.local_classifier import LOCAL_CLASSIFIER
from src.tool_classifier.llm_classifier import LLM_CLASSIFIER
from src.core.event_bus import EventBus
from src.tool_classifier.classifier_helper.json_monitor import JSONMonitor
from src.utils.helpers import TextUtils
from src.tool_classifier.classifier_helper.data_schema import DataManager
from src.utils.config import PROMPT_CLASSIFER_PATH
from src.utils.logger import setup_logging

class PromptClassifier:
    def __init__(self, event_bus: EventBus):
        """Initialize basic components of the classifier manager."""
        self.logger = setup_logging(module_name="Classifier_Manager")
        self.data_manager = None
        self.local_classifier = None
        self.llm_classifier = None
        self.json_monitor = None
        self._monitor_task = None
        self.event_bus = event_bus

    async def initialize(self, json_threshold: int = 50, check_interval: int = 20)-> None:
        """Initialize and load all components asynchronously.
        
        Args:
            json_threshold: Number of items in JSON before triggering update
            check_interval: Interval in seconds to check JSON file
        """
        self.data_manager = DataManager(PROMPT_CLASSIFER_PATH)
        
        # Initialize classifiers asynchronously
        self.local_classifier = LOCAL_CLASSIFIER()
        local_init_task = asyncio.create_task(self.local_classifier.initialize())
        self.llm_classifier = LLM_CLASSIFIER()
        await local_init_task
        
        # Initialize JSON monitor
        self.json_monitor = JSONMonitor(
            file_path=PROMPT_CLASSIFER_PATH,
            callback=self._handle_json_update,
            check_interval=check_interval,
            data_length=json_threshold
        )
        await self.start_json_monitoring()

        self.event_bus.subscribe(
            topic_name="prompt.classify",
            callback=self.classify_prompt,
            async_handler="True"
        )

    async def shutdown(self) -> None:
        """Shutdown the classifier manager and cleanup resources."""
        if self._monitor_task and not self._monitor_task.done():
            self.logger.info("Stopping JSON monitor...")
            self.json_monitor.stop()
            self._monitor_task.cancel()
    
    async def start_json_monitoring(self) -> None:
        """Start the classifier manager and monitoring."""
        if self._monitor_task is None:
            self.logger.info("Starting JSON monitor...")
            self._monitor_task = asyncio.create_task(self._run_monitor())
            self._monitor_task.add_done_callback(self._handle_monitor_done)

    async def _run_monitor(self) -> None:
        """Run the JSON monitor and handle any exceptions."""
        try:
            await self.json_monitor.monitor_json()
        except Exception as e:
            self.logger.error(f"JSON monitor error: {str(e)}")
    
    def _handle_monitor_done(self, future: asyncio.Future) -> None:
        """Handle completion of the monitor task."""
        try:
            future.result()
        except asyncio.CancelledError:
            self.logger.info("JSON monitor stopped")
        except Exception as e:
            self.logger.error(f"JSON monitor failed: {str(e)}")
    
    async def _handle_json_update(self, data_count: int) -> None:
        """Handle JSON file update by triggering ChromaDB update.
        
        Args:
            data_count: Number of items in the JSON file
        """
        self.logger.info(f"JSON update detected with {data_count} items")
        await self.local_classifier.update_chromadb()
    
    async def classify_prompt(self, prompt: str) -> str:
        """Classify a prompt using the hierarchical classification system.
        
        Args:
            prompt: The text to classify
            
        Returns:
            ClassificationResponse containing the classification result and source
        """
       
        prompt_ID = TextUtils.generate_id(prompt)
        prompt = prompt.strip()

        # Step 1: Check JSON cache
        result = self.data_manager.find_in_cache(prompt_ID=prompt_ID)

        if result is None:
            # Step 2: Try query classifier
            result = await self.local_classifier.classify_query_locally(prompt_ID=prompt_ID, query=prompt)
            
        if result is None:
            # Step 3: Fall back to LLM
            self.logger.info("Falling back to LLM classifier")
            result = self.llm_classifier.handle_llm_classification(prompt_ID=prompt_ID, query=prompt)

        if result is not None:
            self.event_bus.publish(
                topic_name="get.result",
                classification = result
            )
            return
        
        # Default fallback
        self.logger.warning("All classification attempts failed, defaulting to conversation")
        self.event_bus.publish(
                topic_name="prompt.classified",
                classification = "conversation"
            )
        return 

if __name__ == '__main__':
    classifier_manager = PromptClassifier()

    from dotenv import load_dotenv; load_dotenv()
    import time
    
    async def main():
        start_time = time.time()
        await classifier_manager.initialize()
        result = await classifier_manager.classify_prompt(" Can you please one browser and search for the tere naam movie on youtube  ")
        print(result)
        await classifier_manager.shutdown()
        print(f"Total time: {time.time() - start_time:.2f} seconds")
    
    asyncio.run(main())